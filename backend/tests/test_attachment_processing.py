"""
Test suite for OneNote attachment processing.

Tests the fixed approach using HTML parsing instead of the unsupported resources collection endpoint.
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
import httpx
from app.graph_client import GraphOneNoteClient
import json


@pytest.fixture
def mock_graph_client():
    """Create a mock GraphOneNoteClient for testing."""
    # Mock the GraphOneNoteClient to avoid authentication requirements
    with patch('app.graph_client.GraphOneNoteClient.__init__', return_value=None):
        client = GraphOneNoteClient.__new__(GraphOneNoteClient)
        client._client = AsyncMock()
        return client


@pytest.fixture
def sample_onenote_html():
    """Sample OneNote page HTML content with embedded resource references."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>AI Architecture & Research</title></head>
    <body>
        <h1>Performance Benchmarks</h1>
        <p>Here are the benchmark results:</p>
        <div>
            <img src="https://graph.microsoft.com/v1.0/me/onenote/resources/1-abc123def456/content" 
                 alt="Performance Chart" />
        </div>
        <div>
            <object data="https://graph.microsoft.com/v1.0/me/onenote/resources/1-xyz789ghi012/content" 
                    type="application/pdf">
                <p>AI Framework Benchmark 2026</p>
            </object>
        </div>
        <div>
            <a href="https://graph.microsoft.com/v1.0/me/onenote/resources/1-def456abc789/$value">
                Download Vector DB Analysis
            </a>
        </div>
        <p>Architecture diagram:</p>
        <img src="https://graph.microsoft.com/v1.0/me/onenote/resources/1-ghi012xyz345/content" 
             alt="RAG Architecture" />
        <p>Some regular content without resources.</p>
        <embed src="https://graph.microsoft.com/v1.0/me/onenote/resources/1-jkl678mno901/content" 
               type="image/png" />
    </body>
    </html>
    """


class TestAttachmentHTMLParsing:
    """Test HTML parsing to extract resource references."""

    @pytest.mark.asyncio
    async def test_extract_resource_ids_from_html(self, mock_graph_client, sample_onenote_html):
        """Test that resource IDs are correctly extracted from OneNote HTML."""
        
        page_id = "test-page-123"
        
        # Mock the page content retrieval
        with patch.object(mock_graph_client, 'get_page_content', return_value=sample_onenote_html):
            # Mock the resource info requests
            async def mock_get_resource_info(page_id, resource_id):
                mock_responses = {
                    "1-abc123def456": {
                        "id": resource_id,
                        "name": "performance_chart.png",
                        "contentType": "image/png",
                        "size": 125000,
                        "downloadUrl": f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"
                    },
                    "1-xyz789ghi012": {
                        "id": resource_id,
                        "name": "AI_Framework_Benchmark_2026.pdf",
                        "contentType": "application/pdf",
                        "size": 2500000,
                        "downloadUrl": f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"
                    },
                    "1-def456abc789": {
                        "id": resource_id,
                        "name": f"resource_{resource_id}.xlsx",
                        "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "size": 750000,
                        "downloadUrl": f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"
                    },
                    "1-ghi012xyz345": {
                        "id": resource_id,
                        "name": f"resource_{resource_id}.png",
                        "contentType": "image/png",
                        "size": 89000,
                        "downloadUrl": f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"
                    },
                    "1-jkl678mno901": {
                        "id": resource_id,
                        "name": f"resource_{resource_id}.png",
                        "contentType": "image/png",
                        "size": 156000,
                        "downloadUrl": f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"
                    }
                }
                
                if resource_id in mock_responses:
                    response = mock_responses[resource_id]
                    # Mock processable attachment check
                    processable_types = ["application/pdf", "image/png", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
                    if response["contentType"] in processable_types:
                        return response
                return None
            
            with patch.object(mock_graph_client, '_get_resource_info', side_effect=mock_get_resource_info):
                attachments = await mock_graph_client.list_page_attachments(page_id)
        
        # Verify we found all expected resources
        assert len(attachments) == 5, f"Expected 5 attachments, got {len(attachments)}"
        
        # Verify expected resource IDs are found
        found_ids = {att["id"] for att in attachments}
        expected_ids = {"1-abc123def456", "1-xyz789ghi012", "1-def456abc789", "1-ghi012xyz345", "1-jkl678mno901"}
        assert found_ids == expected_ids, f"Expected {expected_ids}, got {found_ids}"
        
        # Verify content types are correctly identified
        pdf_attachments = [att for att in attachments if att["contentType"] == "application/pdf"]
        assert len(pdf_attachments) == 1, "Should find 1 PDF attachment"
        assert pdf_attachments[0]["name"] == "AI_Framework_Benchmark_2026.pdf"
        
        png_attachments = [att for att in attachments if att["contentType"] == "image/png"]
        assert len(png_attachments) == 3, "Should find 3 PNG attachments"
        
        xlsx_attachments = [att for att in attachments if att["contentType"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
        assert len(xlsx_attachments) == 1, "Should find 1 XLSX attachment"


class TestResourceMetadataRetrieval:
    """Test resource metadata retrieval using HEAD requests."""
    
    @pytest.mark.asyncio
    async def test_get_resource_info_success(self, mock_graph_client):
        """Test successful resource info retrieval."""
        
        resource_id = "1-abc123def456"
        
        # Mock HTTP client and response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-length": "2500000",
            "content-disposition": 'attachment; filename="test_document.pdf"'
        }
        
        mock_client = AsyncMock()
        mock_client.head.return_value = mock_response
        
        with patch.object(mock_graph_client, '_client_ctx', return_value=mock_client):
            result = await mock_graph_client._get_resource_info("test-page", resource_id)
        
        assert result is not None
        assert result["id"] == resource_id
        assert result["name"] == "test_document.pdf"
        assert result["contentType"] == "application/pdf"
        assert result["size"] == 2500000
        assert result["downloadUrl"] == f"https://graph.microsoft.com/v1.0/me/onenote/resources/{resource_id}/content"


class TestAttachmentDownload:
    """Test attachment content download."""
    
    @pytest.mark.asyncio
    async def test_download_attachment_success(self, mock_graph_client):
        """Test successful attachment download."""
        
        attachment_id = "1-abc123def456"
        expected_content = b"fake PDF content here"
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.content = expected_content
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        with patch.object(mock_graph_client, '_client_ctx', return_value=mock_client):
            content = await mock_graph_client.get_attachment_content("test-page", attachment_id)
        
        assert content == expected_content
        mock_client.get.assert_called_once_with(f"https://graph.microsoft.com/v1.0/me/onenote/resources/{attachment_id}/content")


if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], cwd=r"d:\repos\onenote\backend")
    
    sys.exit(result.returncode)
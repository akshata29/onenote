from typing import Dict, List, Optional, Any
import logging
import asyncio
from io import BytesIO

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient as AsyncDocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    DocumentAnalysisFeature,
    ContentFormat
)

from .config import get_settings

logger = logging.getLogger(__name__)


class DocumentIntelligenceClient:
    """
    Azure Document Intelligence client for processing attachments and extracting content.
    """
    
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.document_intelligence_api_key
        self.endpoint = self.settings.document_intelligence_endpoint
        
        # Check if Document Intelligence is configured
        if not self.endpoint or not self.api_key:
            logger.warning("Document Intelligence not configured - attachment processing will be limited")
            self.client = None
        else:
            self.client = AsyncDocumentIntelligenceClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
        
        # Supported file extensions
        self.supported_extensions = set(
            self.settings.supported_attachment_types.lower().split(',')
        )
        
    async def analyze_document(
        self, 
        file_content: bytes, 
        filename: str,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a document using Document Intelligence.
        
        Args:
            file_content: The document content as bytes
            filename: Original filename for type detection
            content_type: MIME type of the file
            
        Returns:
            Dict containing extracted content and metadata
        """
        # Check if Document Intelligence is available
        if not self.client:
            logger.warning("Document Intelligence not available - returning basic metadata")
            return {
                "success": False,
                "error": "Document Intelligence not configured",
                "content": f"[Attachment: {filename}]",
                "metadata": {
                    "filename": filename,
                    "file_size": len(file_content),
                    "content_type": content_type or "unknown"
                }
            }
            
        try:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            logger.info(f"📄 Processing document: {filename} (type: {file_ext}, size: {len(file_content)} bytes)")
            
            if file_ext not in self.supported_extensions:
                logger.error(f"❌ Unsupported file type: {file_ext} (supported: {self.supported_extensions})")
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "content": "",
                    "metadata": {"filename": filename, "error_reason": "unsupported_type"}
                }
            
            logger.info(f"✅ File type {file_ext} is supported - starting Document Intelligence analysis for {filename}")
            
            # Use layout model for comprehensive extraction
            # Create AnalyzeDocumentRequest with bytes_source (per Microsoft documentation)
            analyze_request = AnalyzeDocumentRequest(bytes_source=file_content)
            
            logger.info(f"🔍 Calling Document Intelligence API for {filename}...")
            
            # Call API with AnalyzeDocumentRequest
            poller = await self.client.begin_analyze_document(
                "prebuilt-layout",
                analyze_request,
                features=[
                    DocumentAnalysisFeature.LANGUAGES,
                    DocumentAnalysisFeature.KEY_VALUE_PAIRS
                ],
                output_content_format=ContentFormat.MARKDOWN
            )
            
            logger.info(f"🔄 Document Intelligence analysis started for {filename}, waiting for results...")
            result: AnalyzeResult = await poller.result()
            logger.info(f"✅ Document Intelligence analysis completed for {filename}")
            logger.info(f"📊 Result summary - Pages: {len(result.pages or [])}, Tables: {len(result.tables or [])}, Content length: {len(result.content or '')}")
            
            return await self._process_analysis_result(result, filename, file_ext)
            
        except Exception as e:
            logger.error(f"❌ Document Intelligence analysis failed for {filename}: {str(e)}")
            logger.exception("Full error details:")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "metadata": {"filename": filename, "error_reason": "analysis_failed"}
            }
    
    async def _process_analysis_result(
        self, 
        result: AnalyzeResult, 
        filename: str, 
        file_ext: str
    ) -> Dict[str, Any]:
        """
        Process the Document Intelligence analysis result.
        """
        try:
            logger.info(f"📝 Processing analysis result for {filename} ({file_ext})")
            
            # Extract main content
            content = result.content or ""
            logger.info(f"📄 Main content extracted: {len(content)} characters")
            
            # Extract tables as structured text
            tables_content = []
            if result.tables:
                logger.info(f"📊 Processing {len(result.tables)} tables")
                for table_idx, table in enumerate(result.tables):
                    table_text = f"\n## Table {table_idx + 1}\n"
                    table_text += f"Rows: {table.row_count}, Columns: {table.column_count}\n\n"
                    
                    # Create table in markdown format
                    rows = {}
                    for cell in table.cells:
                        if cell.row_index not in rows:
                            rows[cell.row_index] = {}
                        rows[cell.row_index][cell.column_index] = cell.content or ""
                    
                    if rows:
                        max_cols = max(max(row.keys()) for row in rows.values()) + 1
                        for row_idx in sorted(rows.keys()):
                            row_data = []
                            for col_idx in range(max_cols):
                                row_data.append(rows[row_idx].get(col_idx, ""))
                            table_text += "| " + " | ".join(row_data) + " |\n"
                            if row_idx == 0:  # Add header separator
                                table_text += "| " + " | ".join(["---"] * max_cols) + " |\n"
                    
                    tables_content.append(table_text)
            
            # Extract key-value pairs
            key_value_pairs = []
            if result.key_value_pairs:
                for kv_pair in result.key_value_pairs:
                    if kv_pair.key and kv_pair.value:
                        key_content = kv_pair.key.content if kv_pair.key.content else ""
                        value_content = kv_pair.value.content if kv_pair.value.content else ""
                        if key_content and value_content:
                            key_value_pairs.append({
                                "key": key_content,
                                "value": value_content,
                                "key_confidence": kv_pair.key.confidence if hasattr(kv_pair.key, 'confidence') else 0.0,
                                "value_confidence": kv_pair.value.confidence if hasattr(kv_pair.value, 'confidence') else 0.0
                            })
            
            # Detect languages
            languages = []
            if result.languages:
                for lang in result.languages:
                    languages.append({
                        "locale": lang.locale,
                        "confidence": lang.confidence
                    })
            
            # Combine all content
            full_content = content
            if tables_content:
                full_content += "\n\n" + "\n\n".join(tables_content)
            
            # Extract metadata
            metadata = {
                "attachment_filename": filename,
                "attachment_filetype": file_ext,
                "page_count": len(result.pages) if result.pages else 0,
                "table_count": len(result.tables) if result.tables else 0,
                "languages": languages,
                "key_value_pairs": key_value_pairs,
                "has_handwritten_content": any(
                    style.is_handwritten for style in result.styles
                ) if result.styles else False,
                "character_count": len(full_content),
                "processing_model": result.model_id
            }
            
            return {
                "success": True,
                "content": full_content,
                "metadata": metadata,
                "raw_content": content,
                "tables_content": tables_content
            }
            
        except Exception as e:
            logger.error(f"Error processing analysis result: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "metadata": {}
            }
    
    async def close(self) -> None:
        """Close the client connection."""
        if self.client:
            await self.client.close()

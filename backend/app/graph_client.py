import asyncio
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from .auth import acquire_graph_token_on_behalf_of, acquire_graph_token_client_credentials
from .config import get_settings
from .telemetry import instrument_async_client

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphOneNoteClient:
    def __init__(self, user_assertion: str) -> None:
        self.settings = get_settings()
        self.scopes = ["https://graph.microsoft.com/.default"]
        self.user_assertion = user_assertion
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_ctx(self) -> httpx.AsyncClient:
        if self._client is None:
            token = acquire_graph_token_on_behalf_of(self.user_assertion, self.scopes)
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"}, timeout=30.0
            )
            instrument_async_client(self._client)
        return self._client

    async def list_notebooks(self) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks")
            resp.raise_for_status()
            return resp.json().get("value", [])
        except Exception as e:
            print(f"OneNote API error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            # Return empty list for now to allow UI to load
            return []

    async def list_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections")
            resp.raise_for_status()
            return resp.json().get("value", [])
        except Exception as e:
            print(f"OneNote sections API error: {e}")
            return []

    async def list_pages(self, section_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/sections/{section_id}/pages")
            resp.raise_for_status()
            return resp.json().get("value", [])
        except Exception as e:
            print(f"OneNote pages API error: {e}")
            return []

    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/content")
            resp.raise_for_status()
            html = resp.text
            text = md(html, heading_style="ATX")
            return {"html": html, "text": text}
        except Exception as e:
            print(f"OneNote page content API error: {e}")
            return {"html": "", "text": ""}

    async def get_resources(self, page_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        try:
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/resources")
            resp.raise_for_status()
            return resp.json().get("value", [])
        except Exception as e:
            print(f"OneNote resources API error: {e}")
            return []

    async def download_resource(self, resource_url: str) -> bytes:
        client = await self._client_ctx()
        resp = await client.get(resource_url)
        resp.raise_for_status()
        return resp.content
    
    async def list_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """
        List all attachments (resources) for a specific page.
        Returns a list of attachment metadata.
        """
        try:
            resources = await self.get_resources(page_id)
            attachments = []
            
            for resource in resources:
                # Filter to include only file attachments (not images embedded in content)
                content_type = resource.get("contentType", "")
                if self._is_processable_attachment(content_type):
                    attachments.append({
                        "id": resource.get("id"),
                        "name": resource.get("name", "unnamed_attachment"),
                        "contentType": content_type,
                        "size": resource.get("size", 0),
                        "downloadUrl": resource.get("downloadUrl"),
                        "createdDateTime": resource.get("createdDateTime"),
                        "lastModifiedDateTime": resource.get("lastModifiedDateTime")
                    })
            
            return attachments
        except Exception as e:
            print(f"OneNote attachments API error: {e}")
            return []
    
    async def get_attachment_content(self, page_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download the content of a specific attachment.
        """
        try:
            resources = await self.get_resources(page_id)
            
            # Find the specific attachment
            target_resource = None
            for resource in resources:
                if resource.get("id") == attachment_id:
                    target_resource = resource
                    break
            
            if not target_resource:
                print(f"Attachment {attachment_id} not found in page {page_id}")
                return None
            
            download_url = target_resource.get("downloadUrl")
            if not download_url:
                print(f"No download URL for attachment {attachment_id}")
                return None
            
            return await self.download_resource(download_url)
            
        except Exception as e:
            print(f"OneNote attachment download error: {e}")
            return None
    
    def _is_processable_attachment(self, content_type: str) -> bool:
        """
        Check if the content type represents a processable attachment.
        """
        processable_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
            "text/plain",  # .txt
            "image/jpeg",  # .jpg, .jpeg
            "image/png",  # .png
            "application/msword",  # .doc
            "application/vnd.ms-excel",  # .xls
            "application/vnd.ms-powerpoint"  # .ppt
        ]
        
        return any(content_type.startswith(ptype) for ptype in processable_types)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> "GraphOneNoteClient":
        await self._client_ctx()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

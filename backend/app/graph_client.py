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
            # Configure connection limits and timeouts to prevent connection leaks
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            timeout = httpx.Timeout(30.0, connect=5.0)
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"}, 
                timeout=timeout,
                limits=limits
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

    async def _get_resource_info(self, page_id: str, resource_id: str, filename_map: dict = None) -> Dict[str, Any]:
        """Get resource info by making a GET request with Range header since HEAD is not supported."""
        client = await self._client_ctx()
        try:
            # Try to get filename from provided mapping first
            name = f"resource_{resource_id}"
            if filename_map and resource_id in filename_map:
                name = filename_map[resource_id]
                print(f"🎯 Using filename from HTML: {name}")
            
            # OneNote doesn't support HEAD requests - use GET with Range to minimize data transfer
            headers = {"Range": "bytes=0-0"}  # Request just the first byte
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/resources/{resource_id}/content", headers=headers)
            
            # Handle both 200 (full content) and 206 (partial content) responses
            if resp.status_code not in [200, 206]:
                resp.raise_for_status()
            
            content_type = resp.headers.get("content-type", "application/octet-stream")
            content_length = resp.headers.get("content-length", "0") 
            
            # For partial content responses, get the real size from Content-Range header
            if resp.status_code == 206:
                content_range = resp.headers.get("content-range", "")
                if content_range:
                    # Format: "bytes 0-0/12345" - extract the total size after the slash
                    import re
                    range_match = re.search(r'/(\d+)', content_range)
                    if range_match:
                        content_length = range_match.group(1)
            
            # If we still have 0 or small size but have a valid filename with extension, assume it's a real file
            if (int(content_length) if content_length.isdigit() else 0) < 100 and name and '.' in name:
                # Use a reasonable default size for known file types to indicate it's processable
                extension = name.lower().split('.')[-1] if '.' in name else ""
                if extension in ['pdf', 'docx', 'xlsx', 'pptx', 'doc', 'xls', 'ppt', 'txt', 'png', 'jpg', 'jpeg', 'csv']:
                    content_length = "1024"  # Default to 1KB to indicate it's a real file
                    print(f"📏 Using default size for attachment with known extension: {name}")
            
            # If no filename mapping found, try to determine filename from content-disposition or guess from content-type
            if not (filename_map and resource_id in filename_map):
                content_disp = resp.headers.get("content-disposition", "")
                if "filename=" in content_disp:
                    import re
                    filename_match = re.search(r'filename="?([^"\s]+)"?', content_disp)
                    if filename_match:
                        name = filename_match.group(1)
                else:
                    # Guess extension from content type
                    ext_map = {
                        "application/pdf": ".pdf",
                        "image/png": ".png", 
                        "image/jpeg": ".jpg",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                        "text/plain": ".txt"
                    }
                    ext = ext_map.get(content_type, "")
                    if ext:
                        name = f"resource_{resource_id}{ext}"
            
            # If content type is generic, infer it from filename
            if content_type == "application/octet-stream" and name:
                extension = name.lower().split('.')[-1] if '.' in name else ""
                content_type_map = {
                    "pdf": "application/pdf",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    "doc": "application/msword",
                    "xls": "application/vnd.ms-excel",
                    "ppt": "application/vnd.ms-powerpoint",
                    "txt": "text/plain",
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "csv": "text/csv"
                }
                inferred_type = content_type_map.get(extension, content_type)
                if inferred_type != content_type:
                    print(f"🔄 Inferred content type from filename: {extension} -> {inferred_type}")
                    content_type = inferred_type
            
            print(f"✅ Resource metadata: {name} ({content_type}, {content_length} bytes)")
            
            return {
                "id": resource_id,
                "name": name,
                "contentType": content_type,
                "size": int(content_length) if content_length.isdigit() else 0,
                "downloadUrl": f"{GRAPH_BASE}/me/onenote/resources/{resource_id}/content"
            }
        except Exception as e:
            print(f"Failed to get resource info for {resource_id}: {e}")
            return None

    async def download_resource(self, resource_url: str) -> bytes:
        client = await self._client_ctx()
        resp = await client.get(resource_url)
        resp.raise_for_status()
        return resp.content
    
    async def list_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Extract attachment references from page HTML content.
        OneNote API doesn't support listing resources collection - we need to parse HTML.
        """
        import re
        from html import unescape
        
        try:
            print(f"\n🔍 ATTACHMENT DEBUG: Starting attachment search for page {page_id}")
            
            # Get page HTML content
            page_content_data = await self.get_page_content(page_id)
            if not page_content_data:
                print(f"❌ DEBUG: No content found for page {page_id}")
                return []
            
            # Extract HTML string from the returned dictionary
            page_content = page_content_data.get("html", "")
            if not page_content:
                print(f"❌ DEBUG: No HTML content found for page {page_id}")
                return []
            
            print(f"📄 DEBUG: Got HTML content, length: {len(page_content)} characters")
            print(f"📄 DEBUG: First 500 chars of HTML: {page_content[:500]}...")
            print(f"📄 DEBUG: Last 500 chars of HTML: ...{page_content[-500:]}")
            
            attachments = []
            
            # Find all resource references in HTML (img, object, embed tags)
            # OneNote stores resources with URLs like: https://graph.microsoft.com/v1.0/users('...')/onenote/resources/{resource-id}/$value
            resource_patterns = [
                # Match the actual OneNote URL structure with users(...) and resource IDs with exclamation marks
                r'<object[^>]*data="[^"]*\/onenote\/resources\/([^\/\$"]+)(?:\/\$value)?[^"]*"[^>]*>',
                r'<img[^>]*src="[^"]*\/onenote\/resources\/([^\/\$"]+)(?:\/\$value)?[^"]*"[^>]*>',
                r'<embed[^>]*src="[^"]*\/onenote\/resources\/([^\/\$"]+)(?:\/\$value)?[^"]*"[^>]*>',
                r'data="[^"]*\/onenote\/resources\/([^\/\$"]+)(?:\/\$value)?[^"]*"',
                r'href="[^"]*\/onenote\/resources\/([^\/\$"]+)(?:\/\$value)?[^"]*"',
                # Additional patterns for PDF attachments specifically
                r'<div[^>]*data-attachment-filename="([^"]*\.pdf)"[^>]*>.*?onenote\/resources\/([^\/\$"]+)',
                r'<span[^>]*>\s*([^<]*\.pdf)\s*</span>.*?onenote\/resources\/([^\/\$"]+)',
                r'<a[^>]*href="[^"]*\/onenote\/resources\/([^\/\$"]+)[^"]*"[^>]*>.*?\.pdf.*?</a>',
                # Look for any reference to resources followed by PDF filename mentions
                r'onenote\/resources\/([^\/\$"]+)(?:\/\$value)?.*?([^\/\s"]*\.pdf)',
                # Fallback pattern for OneNote resource IDs (format: 1-{guid}!1-{section-id})
                r'(1-[a-fA-F0-9]{32}![a-fA-F0-9\-]+)',
            ]
            
            resource_ids = set()
            print(f"\n🔍 DEBUG: Testing {len(resource_patterns)} regex patterns on HTML...")
            
            for i, pattern in enumerate(resource_patterns):
                print(f"📝 DEBUG: Pattern {i+1}: {pattern}")
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                print(f"   → Found {len(matches)} matches: {matches[:5] if matches else 'None'}")
                
                if matches:
                    for match in matches:
                        # Handle both single matches and tuple matches from multi-group patterns
                        if isinstance(match, tuple):
                            # For patterns that return multiple groups, use the resource ID 
                            for item in match:
                                if len(item) >= 8:  # Reasonable resource ID length
                                    resource_ids.add(item)
                                    print(f"   ✅ Added resource ID from tuple: {item}")
                        else:
                            # Single match
                            if len(match) >= 8:  # Reasonable resource ID length
                                resource_ids.add(match)
                                print(f"   ✅ Added resource ID: {match}")
                
            print(f"\n📊 DEBUG: Found {len(resource_ids)} unique resource IDs for page {page_id}")
            if resource_ids:
                print(f"📊 DEBUG: Resource IDs: {list(resource_ids)[:10]}")  # Show first 10
            else:
                print(f"❌ DEBUG: NO RESOURCE IDs FOUND! Looking for common file indicators...")
                # Look for common file indicators
                pdf_count = len(re.findall(r'\.pdf', page_content, re.IGNORECASE))
                xlsx_count = len(re.findall(r'\.xlsx?', page_content, re.IGNORECASE))
                docx_count = len(re.findall(r'\.docx?', page_content, re.IGNORECASE))
                img_tags = len(re.findall(r'<img[^>]*>', page_content, re.IGNORECASE))
                object_tags = len(re.findall(r'<object[^>]*>', page_content, re.IGNORECASE))
                embed_tags = len(re.findall(r'<embed[^>]*>', page_content, re.IGNORECASE))
                
                print(f"📊 DEBUG: File extension mentions - PDF: {pdf_count}, Excel: {xlsx_count}, Word: {docx_count}")
                print(f"📊 DEBUG: HTML tags - IMG: {img_tags}, OBJECT: {object_tags}, EMBED: {embed_tags}")
            
            print(f"Found {len(resource_ids)} unique resource IDs in page HTML: {list(resource_ids)}")
            
            # Extract filename mappings from data-attachment attributes and text content
            filename_map = {}
            
            # Pattern 1: data-attachment attributes
            filename_pattern = r'<object[^>]*data-attachment="([^"]+)"[^>]*data="[^"]*\/onenote\/resources\/([^\/\$"]+)'
            filename_matches = re.findall(filename_pattern, page_content, re.IGNORECASE)
            for filename, resource_id in filename_matches:
                filename_map[resource_id] = filename
                print(f"📁 Found filename mapping: {resource_id} -> {filename}")
            
            # Pattern 2: Look for PDF filenames mentioned near resource IDs
            pdf_filename_pattern = r'([^\/\s"]*\.pdf)\b.*?onenote\/resources\/([^\/\$"]+)'
            pdf_matches = re.findall(pdf_filename_pattern, page_content, re.IGNORECASE)
            for filename, resource_id in pdf_matches:
                if resource_id not in filename_map:  # Don't override existing mappings
                    filename_map[resource_id] = filename
                    print(f"📁 Found PDF filename mapping: {resource_id} -> {filename}")
            
            # Pattern 3: Look for resource IDs mentioned near PDF filenames (reverse order)
            reverse_pdf_pattern = r'onenote\/resources\/([^\/\$"]+).*?([^\/\s"]*\.pdf)\b'
            reverse_matches = re.findall(reverse_pdf_pattern, page_content, re.IGNORECASE)
            for resource_id, filename in reverse_matches:
                if resource_id not in filename_map:  # Don't override existing mappings
                    filename_map[resource_id] = filename
                    print(f"📁 Found reverse PDF filename mapping: {resource_id} -> {filename}")
            
            # Pattern 4: Generic attachment filenames in text content
            attachment_text_pattern = r'<[^>]*>([^<]*[^\s]+\.(pdf|docx?|xlsx?|pptx?|txt|png|jpe?g))</[^>]*>'
            text_matches = re.findall(attachment_text_pattern, page_content, re.IGNORECASE)
            print(f"📁 Found {len(text_matches)} attachment filename mentions in text")
            
            # Get metadata for each resource
            for resource_id in resource_ids:
                try:
                    # Try to get resource metadata by downloading a small portion
                    resource_info = await self._get_resource_info(page_id, resource_id, filename_map)
                    if resource_info and self._is_processable_attachment(resource_info.get("contentType", "")):
                        attachments.append(resource_info)
                except Exception as e:
                    print(f"Failed to get info for resource {resource_id}: {e}")
                    
            print(f"Successfully processed {len(attachments)} attachments")
            return attachments
            
        except Exception as e:
            print(f"OneNote HTML parsing error: {e}")
            return []
    
    async def get_attachment_content(self, page_id: str, attachment_id: str) -> Optional[bytes]:
        """
        Download the content of a specific attachment by resource ID.
        """
        try:
            client = await self._client_ctx()
            resp = await client.get(f"{GRAPH_BASE}/me/onenote/resources/{attachment_id}/content")
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            print(f"OneNote attachment download error for {attachment_id}: {e}")
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

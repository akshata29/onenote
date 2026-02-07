import httpx
from markdownify import markdownify as md
from typing import Any, Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings
from .auth import get_graph_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self, user_assertion: str):
        self.user_assertion = user_assertion
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _client_ctx(self) -> httpx.AsyncClient:
        if self._client is None:
            token = get_graph_token(self.user_assertion)
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"}, timeout=30.0
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_notebooks(self) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_pages(self, section_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/sections/{section_id}/pages")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/content")
        resp.raise_for_status()
        html = resp.text
        text = md(html, heading_style="ATX")
        return {"html": html, "text": text}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def list_resources(self, page_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/resources")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
    async def download_resource(self, resource_url: str) -> bytes:
        client = await self._client_ctx()
        resp = await client.get(resource_url)
        resp.raise_for_status()
        return resp.content

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    async def __aenter__(self) -> "GraphClient":
        await self._client_ctx()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

import httpx
from typing import Any, Dict, List, Optional

from .config import get_settings
from .telemetry import instrument_async_client


class MCPClient:
    def __init__(self, user_token: str | None = None) -> None:
        settings = get_settings()
        self.base_url = settings.mcp_base_url.rstrip("/")
        headers = {}
        if user_token:
            headers["Authorization"] = f"Bearer {user_token}"
        self.client = httpx.AsyncClient(timeout=30.0, headers=headers)
        instrument_async_client(self.client)

    async def search(self, query: str, scope: dict | None = None) -> List[Dict[str, Any]]:
        payload = {"query": query, "scope": scope or {}}
        resp = await self.client.post(f"{self.base_url}/search", json=payload)
        resp.raise_for_status()
        return resp.json().get("results", [])

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        resp = await self.client.get(f"{self.base_url}/pages/{page_id}")
        resp.raise_for_status()
        return resp.json()

    async def list_notebooks(self) -> List[Dict[str, Any]]:
        resp = await self.client.get(f"{self.base_url}/notebooks")
        resp.raise_for_status()
        return resp.json().get("value", [])

    async def list_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        resp = await self.client.get(f"{self.base_url}/notebooks/{notebook_id}/sections")
        resp.raise_for_status()
        return resp.json().get("value", [])

    async def list_pages(self, section_id: str) -> List[Dict[str, Any]]:
        resp = await self.client.get(f"{self.base_url}/sections/{section_id}/pages")
        resp.raise_for_status()
        return resp.json().get("value", [])

    async def extract_content(self, scope: dict | None = None) -> List[Dict[str, Any]]:
        """Extract all content from scope for LLM context"""
        payload = {"scope": scope or {}}
        resp = await self.client.post(f"{self.base_url}/extract", json=payload)
        resp.raise_for_status()
        return resp.json().get("content", [])

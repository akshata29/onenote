import httpx
from typing import Any, Dict, List, Optional

from .config import get_settings
from .telemetry import instrument_async_client


class MCPClient:
    def __init__(self, user_token: str | None = None) -> None:
        settings = get_settings()
        self.base_url = settings.mcp_base_url.rstrip("/")
        self.headers = {}
        if user_token:
            self.headers["Authorization"] = f"Bearer {user_token}"
        self.timeout = 30.0

    async def search(self, query: str, scope: dict | None = None) -> List[Dict[str, Any]]:
        payload = {"query": query, "scope": scope or {}}
        # Configure connection limits and timeout
        limits = httpx.Limits(max_keepalive_connections=3, max_connections=5)
        timeout = httpx.Timeout(self.timeout, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, headers=self.headers, limits=limits) as client:
            instrument_async_client(client)
            resp = await client.post(f"{self.base_url}/search", json=payload)
            resp.raise_for_status()
            return resp.json().get("results", [])

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            instrument_async_client(client)
            resp = await client.get(f"{self.base_url}/pages/{page_id}")
            resp.raise_for_status()
            return resp.json()

    async def list_notebooks(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            instrument_async_client(client)
            resp = await client.get(f"{self.base_url}/notebooks")
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def list_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            instrument_async_client(client)
            resp = await client.get(f"{self.base_url}/notebooks/{notebook_id}/sections")
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def list_pages(self, section_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            instrument_async_client(client)
            resp = await client.get(f"{self.base_url}/sections/{section_id}/pages")
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def extract_content(self, scope: dict | None = None) -> List[Dict[str, Any]]:
        """Extract all content from scope for LLM context"""
        payload = {"scope": scope or {}}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            instrument_async_client(client)
            resp = await client.post(f"{self.base_url}/extract", json=payload)
            resp.raise_for_status()
            return resp.json().get("content", [])

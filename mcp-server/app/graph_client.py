import httpx
from markdownify import markdownify as md
from typing import Any, Dict, List
import asyncio
import logging
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    RetryCallState,
    retry_if_exception_type
)

from .config import get_settings
from .auth import get_graph_token

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def wait_for_rate_limit(retry_state: RetryCallState) -> float:
    """Custom wait strategy for Graph API rate limits"""
    if retry_state.outcome and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        if isinstance(exception, httpx.HTTPStatusError) and exception.response.status_code == 429:
            # Check for Retry-After header
            retry_after = exception.response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
                logger.warning(f"Rate limited, waiting {wait_time} seconds as specified in Retry-After header")
                return wait_time
            else:
                # Fallback to exponential backoff if no header
                wait_time = min(2 ** retry_state.attempt_number, 60)
                logger.warning(f"Rate limited, no Retry-After header, waiting {wait_time} seconds")
                return wait_time
    
    # Default exponential backoff for other retryable errors
    return min(0.5 * (2 ** retry_state.attempt_number), 10)


def should_retry_graph_error(exception: Exception) -> bool:
    """Determine if we should retry based on the exception"""
    if isinstance(exception, httpx.HTTPStatusError):
        # Always retry on rate limits
        if exception.response.status_code == 429:
            return True
        # Retry on server errors
        if 500 <= exception.response.status_code < 600:
            return True
        # Retry on specific transient errors
        if exception.response.status_code in [502, 503, 504]:
            return True
    
    # Retry on network errors
    if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
        return True
    
    return False


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

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
    async def list_notebooks(self) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
    async def list_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/notebooks/{notebook_id}/sections")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
    async def list_pages(self, section_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/sections/{section_id}/pages")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/content")
        resp.raise_for_status()
        html = resp.text
        text = md(html, heading_style="ATX")
        return {"html": html, "text": text}

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
    async def list_resources(self, page_id: str) -> List[Dict[str, Any]]:
        client = await self._client_ctx()
        resp = await client.get(f"{GRAPH_BASE}/me/onenote/pages/{page_id}/resources")
        resp.raise_for_status()
        return resp.json().get("value", [])

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_for_rate_limit,
        retry=should_retry_graph_error,
        reraise=True
    )
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

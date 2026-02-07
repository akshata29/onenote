from typing import Any, Dict, List
from azure.search.documents.aio import SearchClient
from azure.search.documents import SearchItemPaged
from azure.search.documents.models import VectorQuery
from azure.core.credentials import AzureKeyCredential

from .config import get_settings
from .secrets import get_secret


class AISearchClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        api_key = self.settings.search_api_key
        self.client = SearchClient(
            endpoint=self.settings.search_endpoint,
            index_name=self.settings.search_index,
            credential=AzureKeyCredential(api_key),
        )

    async def search(self, query: str, vector: List[float] | None, filters: str | None = None, top: int = 8) -> List[Dict[str, Any]]:
        vector_query = None
        if vector is not None:
            vector_query = VectorQuery(vector=vector, k=top, fields="content_vector")
        results: SearchItemPaged[Any] = await self.client.search(
            search_text=query,
            vector_queries=[vector_query] if vector_query else None,
            filter=filters,
            semantic_configuration=self.settings.ai_search_semantic_config if self.settings.enable_semantic_ranking else None,
            top=top,
        )
        hits: List[Dict[str, Any]] = []
        async for item in results:
            doc = item.copy()
            doc["score"] = item.get("@search.score")
            doc["rerankerScore"] = item.get("@search.rerankerScore")
            hits.append(doc)
        return hits

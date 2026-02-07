import asyncio
import logging
from typing import Dict, List

from .graph_client import GraphOneNoteClient
from .chunking import paragraph_chunks
from .embeddings_client import EmbeddingsClient
from .search_client import AISearchClient
from .config import get_settings

logger = logging.getLogger(__name__)


class IngestionWorker:
    def __init__(self, user_assertion: str):
        self.graph = GraphOneNoteClient(user_assertion)
        self.embedder = EmbeddingsClient()
        self.search = AISearchClient()
        self.settings = get_settings()

    async def ingest_notebook(self, notebook_id: str) -> None:
        sections = await self.graph.list_sections(notebook_id)
        for section in sections:
            await self.ingest_section(section["id"], notebook_id, section.get("displayName"))

    async def ingest_section(self, section_id: str, notebook_id: str, section_name: str | None = None) -> None:
        pages = await self.graph.list_pages(section_id)
        for page in pages:
            await self.ingest_page(page["id"], notebook_id, section_id, page.get("title"), section_name)

    async def ingest_page(self, page_id: str, notebook_id: str, section_id: str, title: str | None, section_name: str | None) -> None:
        page_content = await self.graph.get_page_content(page_id)
        text = page_content["text"]
        chunks = paragraph_chunks(text, self.settings.chunk_size, self.settings.chunk_overlap)
        contents = [c["content"] for c in chunks]
        vectors = await self.embedder.embed(contents)
        docs: List[Dict] = []
        for idx, chunk in enumerate(chunks):
            docs.append(
                {
                    "id": f"{page_id}-{idx}",
                    "content": chunk["content"],
                    "content_vector": vectors[idx],
                    "page_id": page_id,
                    "page_title": title,
                    "section_id": section_id,
                    "section_name": section_name,
                    "notebook_id": notebook_id,
                    "source_type": "page",
                }
            )
        await self.search.client.upload_documents(docs)

    async def close(self) -> None:
        await self.graph.close()
        await self.search.client.close()


async def run_notebook_ingestion(user_assertion: str, notebook_id: str) -> None:
    worker = IngestionWorker(user_assertion)
    try:
        await worker.ingest_notebook(notebook_id)
    finally:
        await worker.close()

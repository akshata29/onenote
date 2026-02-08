from typing import Dict, List, Any
import httpx

from .embeddings_client import EmbeddingsClient
from .search_client import AISearchClient
from .mcp_adapter import MCPClient
from .graph_client import GraphOneNoteClient
from .chunking import paragraph_chunks
from .config import get_settings


class RAGOrchestrator:
    def __init__(self, user_assertion: str):
        self.settings = get_settings()
        self.embedder = EmbeddingsClient()
        self.search_client = AISearchClient()
        self.mcp = MCPClient(user_token=user_assertion)
        self.graph_client = GraphOneNoteClient(user_assertion)
        self.user_assertion = user_assertion

    async def close(self):
        """Close any open HTTP clients to prevent connection leaks."""
        if hasattr(self.graph_client, 'close'):
            await self.graph_client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def answer_with_search(
        self, 
        message: str, 
        filters: dict | None = None,
        search_mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """
        Enhanced search with advanced filtering and search modes.
        """
        vector = (await self.embedder.embed([message]))[0]
        
        # Build filter query from structured filters
        filter_query = None
        if filters:
            filter_query = self.search_client.build_filter_query(
                notebook_ids=filters.get("notebook_ids"),
                section_ids=filters.get("section_ids"),
                page_ids=filters.get("page_ids"),
                content_types=filters.get("content_types"),
                date_range=filters.get("date_range"),
                attachment_types=filters.get("attachment_types"),
                has_attachments=filters.get("has_attachments")
            )
        
        hits = await self.search_client.search(
            query=message, 
            vector=vector, 
            filters=filter_query,
            search_mode=search_mode
        )
        
        # Extract content from search hits for LLM context
        context_parts = []
        for hit in hits:
            # Build rich context from each search hit
            title = hit.get("page_title", "Untitled")
            content = hit.get("content", "").strip()
            notebook = hit.get("notebook_name", "")
            section = hit.get("section_name", "")
            
            if content:
                # Add metadata for better context
                context_header = f"Source: {title}"
                if notebook and section:
                    context_header += f" (from {notebook} → {section})"
                elif notebook:
                    context_header += f" (from {notebook})"
                
                context_parts.append(f"{context_header}\n{content}")
        
        # Use LLM to generate intelligent answer from search context
        full_context = "\n\n---\n\n".join(context_parts)
        answer = await self._answer_with_llm(message, full_context) if context_parts else "No relevant information found in your OneNote content."
        
        citations = []
        for h in hits:
            citation = {
                "page_id": h.get("page_id"),
                "page_title": h.get("page_title"),
                "section_id": h.get("section_id"),
                "section_name": h.get("section_name"),
                "notebook_id": h.get("notebook_id"),
                "notebook_name": h.get("notebook_name"),
                "content_type": h.get("content_type"),
                "score": h.get("score"),
                "reranker_score": h.get("rerankerScore"),
                "source_type": h.get("source_type")
            }
            
            # Add attachment metadata if present
            if h.get("attachment_filename"):
                citation.update({
                    "attachment_filename": h.get("attachment_filename"),
                    "attachment_filetype": h.get("attachment_filetype"),
                    "attachment_page_count": h.get("attachment_page_count"),
                    "attachment_table_count": h.get("attachment_table_count")
                })
            
            citations.append(citation)
        
        return {
            "answer": answer, 
            "citations": citations, 
            "mode": "search",
            "search_mode": search_mode,
            "filter_applied": filter_query is not None,
            "total_results": len(hits)
        }

    async def answer_with_mcp(self, message: str, scope: dict | None = None) -> Dict[str, Any]:
        # Extract all content from scope
        content_items = await self.mcp.extract_content(scope)
        
        # Build context from all content
        context_parts = []
        for item in content_items:
            title = item.get("page_title", "Untitled")
            content = item.get("content", "")
            if content.strip():
                context_parts.append(f"Page: {title}\n{content}")
        
        full_context = "\n\n---\n\n".join(context_parts)
        
        # Use OpenAI to answer based on full context
        answer = await self._answer_with_llm(message, full_context)
        
        # Create citations from content items
        citations = [
            {
                "page_title": item.get("page_title"),
                "page_id": item.get("page_id"),
                "content": item.get("content", "")[:500] + "..." if len(item.get("content", "")) > 500 else item.get("content", "")
            }
            for item in content_items if item.get("content", "").strip()
        ]
        
        return {"answer": answer, "citations": citations, "mode": "mcp"}

    async def get_search_facets(self, query: str = "*") -> Dict[str, List[Dict]]:
        """Get facet information for building filter UI."""
        return await self.search_client.get_facets(query)
    
    async def get_search_suggestions(self, query: str, top: int = 5) -> List[str]:
        """Get search suggestions for autocomplete."""
        return await self.search_client.get_search_suggestions(query, top)

    async def _answer_with_llm(self, question: str, context: str) -> str:
        """Use OpenAI to answer question based on provided context"""
        # Enhanced system prompt for RAG responses
        system_prompt = """You are an intelligent AI assistant that helps users find information from their OneNote content. 

Guidelines for responding:
- Provide specific, accurate answers based on the provided OneNote content
- If the information isn't in the content, clearly state that the information wasn't found
- Reference specific pages, sections, or documents when relevant  
- Be direct and concise while being comprehensive
- Use natural language that flows well
- When presenting structured data (like budgets, timelines, lists), format them clearly
- If multiple sources contain related information, synthesize them thoughtfully
- Maintain the context and relationships between different pieces of information

Remember: You are answering based on the user's actual OneNote content, so confidence in your responses should reflect the clarity and completeness of the source material."""
        
        user_prompt = f"""Based on the following OneNote content, please answer this question: {question}

OneNote Content:
{context}

Question: {question}

Please provide a clear, helpful answer based on the content above."""
        
        # Use Azure OpenAI chat completions  
        url = f"{self.settings.openai_endpoint.rstrip('/')}/openai/deployments/{self.settings.openai_chat_deployment_name}/chat/completions?api-version={self.settings.openai_api_version}"
        headers = {
            "api-key": self.settings.openai_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1500,
            "temperature": 0.1
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            return data["choices"][0]["message"]["content"]

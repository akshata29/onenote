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
        self.user_assertion = user_assertion

    async def answer_with_search(self, message: str, filters: str | None = None) -> Dict[str, Any]:
        vector = (await self.embedder.embed([message]))[0]
        hits = await self.search_client.search(message, vector, filters=filters)
        snippets = [h.get("content", "") for h in hits]
        answer = self._compose(snippets, message)
        citations = [
            {
                "page_id": h.get("page_id"),
                "page_title": h.get("page_title"),
                "section_id": h.get("section_id"),
                "notebook_id": h.get("notebook_id"),
                "score": h.get("score"),
            }
            for h in hits
        ]
        return {"answer": answer, "citations": citations, "mode": "search"}

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

    def _compose(self, snippets: List[str], question: str) -> str:
        body = "\n".join(f"- {s}" for s in snippets if s)
        return f"Based on OneNote, here is what I found about '{question}':\n{body}"

    async def _answer_with_llm(self, question: str, context: str) -> str:
        """Use OpenAI to answer question based on full context"""
        # Construct the prompt
        system_prompt = """You are a helpful AI assistant. Answer the user's question based on the provided OneNote content.
        
Guidelines:
- Provide specific, accurate answers based on the content
- If the information isn't in the content, say so clearly
- Reference specific pages or sections when relevant
- Be concise but comprehensive
"""
        
        user_prompt = f"""Based on the following OneNote content, please answer this question: {question}

OneNote Content:
{context}

Question: {question}
"""
        
        # Use Azure OpenAI chat completions  
        url = f"{self.settings.openai_endpoint.rstrip('/')}/openai/deployments/{self.settings.openai_chat_deployment_name}/chat/completions?api-version=2024-06-01"
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

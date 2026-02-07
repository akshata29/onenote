from typing import List

import httpx

from .config import get_settings
from .secrets import get_secret


class EmbeddingsClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.endpoint = self.settings.openai_endpoint.rstrip("/")
        self.model = self.settings.openai_embedding_model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.endpoint}/openai/deployments/{self.model}/embeddings?api-version=2023-05-15"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json={"input": texts})
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]

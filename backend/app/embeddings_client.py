from typing import List

import httpx

from .config import get_settings


class EmbeddingsClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.openai_api_key
        self.endpoint = self.settings.openai_endpoint.rstrip("/")
        self.deployment = self.settings.openai_embedding_deployment_name

    async def embed(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.endpoint}/openai/deployments/{self.deployment}/embeddings?api-version={self.settings.openai_api_version}"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json={"input": texts})
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]

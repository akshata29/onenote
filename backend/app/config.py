from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # tolerate extra env keys
    )

    app_name: str = "onenote-rag"
    api_version: str = "v1"
    tenant_id: str
    client_id: str
    client_secret: str  # env var name or KV secret name; local-friendly
    authority: str | None = None
    allowed_audiences: str = ""
    key_vault_url: str | None = None
    storage_account_url: str | None = None
    search_endpoint: str
    search_index: str
    search_api_key_secret_name: str
    search_api_key: str
    openai_endpoint: str
    openai_api_key_secret_name: str
    openai_api_key: str
    openai_embedding_model: str | None = None
    openai_embedding_deployment_name: str | None = None
    openai_chat_deployment_name: str = "gpt-4o"
    mcp_base_url: str
    app_insights_connection_string: str | None = None
    log_analytics_workspace_id: str | None = None
    enable_semantic_ranking: bool = True
    ai_search_semantic_config: str | None = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retries: int = 3
    retry_backoff: float = 0.5

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        # allow either env var name
        if not self.openai_embedding_model and self.openai_embedding_deployment_name:
            self.openai_embedding_model = self.openai_embedding_deployment_name

@lru_cache()
def get_settings() -> Settings:
    return Settings()

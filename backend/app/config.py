from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "onenote-rag"
    api_version: str = "v1"
    tenant_id: str
    client_id: str
    client_secret: str
    authority: str | None = None
    allowed_audiences: str = ""
    key_vault_url: str | None = None
    storage_account_url: str | None = None
    
    # Search configuration - direct from .env
    search_endpoint: str
    search_index: str = "onenote-index"
    search_api_key: str
    
    # OpenAI configuration - direct from .env
    openai_endpoint: str
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"
    openai_embedding_deployment_name: str = "embedding"
    openai_chat_deployment_name: str = "chat4o"
    
    # Document Intelligence configuration - direct from .env
    document_intelligence_endpoint: str | None = None
    document_intelligence_api_key: str | None = None
    
    # MCP and other services
    mcp_base_url: str
    app_insights_connection_string: str | None = None
    ai_search_semantic_config: str | None = "default"
    
    # Enhanced search settings
    enable_attachment_processing: bool = True
    max_attachment_size_mb: int = 30
    supported_attachment_types: str = "pdf,docx,xlsx,pptx,txt,jpg,jpeg,png"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_retries: int = 3
    retry_backoff: float = 0.5
    enable_semantic_ranking: bool = True
    
    # API versions
    search_api_version: str = "2023-11-01"
    openai_api_version: str = "2024-08-01-preview"
    document_intelligence_api_version: str = "2024-07-31-preview"
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
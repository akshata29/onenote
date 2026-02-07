from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    tenant_id: str
    client_id: str
    client_secret: str
    authority: str | None = None
    app_name: str = "onenote-mcp-server"
    max_pages_sample: int = 50
    chunk_size: int = 900
    chunk_overlap: int = 150
    include_attachments: bool = False  # Changed default to False for better performance

    def __init__(self, **data):
        super().__init__(**data)
        if not self.authority:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

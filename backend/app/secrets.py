import os
from functools import lru_cache
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from .config import get_settings


@lru_cache()
def _client() -> Optional[SecretClient]:
    settings = get_settings()
    if not settings.key_vault_url:
        return None
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=settings.key_vault_url, credential=credential)


def get_secret(secret_name: str) -> str:
    # Local-friendly: prefer environment variable with same name; fall back to Key Vault if configured.
    env_val = os.getenv(secret_name)
    if env_val:
        return env_val
    client = _client()
    if client is None:
        raise RuntimeError(f"Secret '{secret_name}' not found in env and no Key Vault configured")
    vault_secret = client.get_secret(secret_name)
    return vault_secret.value


def get_env_or_secret(env_name: str, secret_name: str) -> str:
    value = os.getenv(env_name)
    if value:
        return value
    return get_secret(secret_name)

import time
from typing import Any, Optional
import jwt
from fastapi import Depends, HTTPException, Request, status
from msal import ConfidentialClientApplication

from .config import get_settings
from .secrets import get_secret


class TokenValidator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.authority = self.settings.authority
        self.audience = set(
            a.strip() for a in (self.settings.allowed_audiences or "").split(",") if a.strip()
        )

    def __call__(self, request: Request) -> dict[str, Any]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
        token = auth_header.split(" ", 1)[1]
        try:
            decoded = jwt.decode(token, options={"verify_signature": False, "verify_aud": False})
        except jwt.PyJWTError as exc:  # type: ignore[attr-defined]
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")
        exp = decoded.get("exp")
        if exp and exp < int(time.time()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        aud = decoded.get("aud")
        if aud and aud not in self.audience:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
        return {"decoded": decoded, "access_token": token}


auth_validator = TokenValidator()


def acquire_graph_token_on_behalf_of(user_assertion: str, scopes: list[str]) -> str:
    settings = get_settings()
    # Use client_secret directly since it contains the actual secret value in local dev
    client_secret = settings.client_secret
    print(f"OBO: Using client_id: {settings.client_id}")
    print(f"OBO: Using authority: {settings.authority}")
    print(f"OBO: Requesting scopes: {scopes}")
    
    app = ConfidentialClientApplication(
        client_id=settings.client_id,
        client_credential=client_secret,
        authority=settings.authority,
    )
    result = app.acquire_token_on_behalf_of(user_assertion=user_assertion, scopes=scopes)
    print(f"OBO result: {result}")
    
    if "access_token" not in result:
        error_desc = result.get('error_description', 'Unknown error')
        print(f"OBO failed: {error_desc}")
        raise HTTPException(status_code=401, detail=f"Failed to acquire OBO token: {error_desc}")
    return result["access_token"]


def acquire_graph_token_client_credentials(scopes: list[str]) -> str:
    settings = get_settings()
    client_secret = settings.client_secret
    print(f"Client Credentials: Using client_id: {settings.client_id}")
    print(f"Client Credentials: Using authority: {settings.authority}")
    print(f"Client Credentials: Requesting scopes: {scopes}")
    
    app = ConfidentialClientApplication(
        client_id=settings.client_id,
        client_credential=client_secret,
        authority=settings.authority,
    )
    result = app.acquire_token_for_client(scopes=scopes)
    print(f"Client Credentials result: {result}")
    
    if "access_token" not in result:
        error_desc = result.get('error_description', 'Unknown error')
        print(f"Client Credentials failed: {error_desc}")
        raise HTTPException(status_code=401, detail=f"Failed to acquire client credentials token: {error_desc}")
    return result["access_token"]

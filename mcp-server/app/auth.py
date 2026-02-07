import time
from typing import Dict
import jwt
from fastapi import Depends, HTTPException, Request, status
from msal import ConfidentialClientApplication

from .config import get_settings


def _obo(user_assertion: str, scopes: list[str]) -> str:
    settings = get_settings()
    app = ConfidentialClientApplication(
        client_id=settings.client_id,
        client_credential=settings.client_secret,
        authority=settings.authority,
    )
    result = app.acquire_token_on_behalf_of(user_assertion=user_assertion, scopes=scopes)
    if "access_token" not in result:
        raise HTTPException(status_code=401, detail=result.get("error_description", "OBO failed"))
    return result["access_token"]


def _decode_bearer(request: Request) -> Dict:
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
    decoded["__raw"] = token
    return decoded


def auth_dependency(request: Request) -> Dict:
    return _decode_bearer(request)


def get_graph_token(user_assertion: str) -> str:
    scopes = ["https://graph.microsoft.com/.default"]
    return _obo(user_assertion, scopes)

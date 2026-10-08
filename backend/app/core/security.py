"""Security and API key authentication utilities."""

from typing import Optional
from fastapi import Header, HTTPException, Security, status
from app.config import settings


def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """Verifies the X-API-Key header against settings.API_KEY.

    If API_KEY is empty in configuration, authentication is bypassed (development mode).
    If API_KEY is set, valid header is strictly enforced.
    """
    if not settings.API_KEY:
        return True

    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header.",
        )
    return True

"""API key authentication middleware."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from amctl.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """Validate the API key from the X-API-Key header."""
    if not api_key or api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

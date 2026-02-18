import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.api_key import ApiKey

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_http_bearer = HTTPBearer(auto_error=False)


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def get_current_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key_header: str | None = Depends(_api_key_header),
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> ApiKey:
    key_value: str | None = None
    if api_key_header:
        key_value = api_key_header.strip()
    elif credentials and credentials.credentials:
        key_value = credentials.credentials.strip()

    if not key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header or Authorization: Bearer <key>.",
        )

    key_hash = _hash_key(key_value)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active.is_(True),
        )
    )
    row = result.scalar_one_or_none()
    print("ROW:", row)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
        )
    return row

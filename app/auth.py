from fastapi import Header, HTTPException, status
from app.security import hash_api_key
from app.db import async_session_maker
from app.repositories import get_active_api_key_by_hash, touch_api_key_used


class AuthContext:
    def __init__(self, tenant_id, api_key_id):
        self.tenant_id = tenant_id
        self.api_key_id = api_key_id

async def require_api_key(authorization: str = Header(...)) -> AuthContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    
    raw_key = authorization.removeprefix("Bearer ").strip()
    if not raw_key:
        raise HTTPException(
            status_code=401, detail="Missing API key"
        )
    
    key_hash = hash_api_key(raw_key)

    async with async_session_maker() as db:
        api_key = await get_active_api_key_by_hash(db, key_hash)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key",
            )
        await touch_api_key_used(db, api_key.id)
        await db.commit()
        return AuthContext(tenant_id=api_key.tenant_id, api_key_id=api_key.id)
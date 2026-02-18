from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.models.api_key import ApiKey

async def get_active_api_key_by_hash(db: AsyncSession, key_hash: str) -> ApiKey | None:
    stmt = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active.is_(True),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def touch_api_key_used(db:AsyncSession, api_key_id):
    stmt = update(ApiKey).where(
        ApiKey.id == api_key_id
    ).values(
        last_used_at = datetime.now(timezone.utc)
    )
    await db.execute(stmt)
import os
import secrets
import uuid
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.models.api_key import Tenant, ApiKey
from app.security import hash_api_key
from app.settings import settings

async def main():
    db_url = os.getenv("DATABASE_URL", settings.database_url)
    engine = create_async_engine(db_url, pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    demo_tenant_name = os.getenv("DEMO_TENANT_NAME", "Demo-tenant")

    async with Session() as db:
        existing = await db.execute(
            select(Tenant).where(Tenant.name ==  demo_tenant_name)
        )
        tenant = existing.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(id = uuid.uuid4(), name=demo_tenant_name)
            db.add(tenant)
            await db.flush()

        raw_key = "aigw+"+secrets.token_urlsafe(24)
        key_hash = hash_api_key(raw_key)

        api_key = ApiKey(id=uuid.uuid4(), tenant_id=tenant.id, key_hash=key_hash, label="demo key")
        db.add(api_key)

        await db.commit()
        
        print("\n=== Demo tenant bootstrapped ===")
        print(f"tenant_name: {demo_tenant_name}")
        print(f"tenant_id:   {tenant.id}")
        print("\n=== Your API key (store it now; it is NOT saved in plaintext) ===")
        print(raw_key)
        print("\nTry:")
        print(f'curl -s http://localhost:8000/v1/predict -H "Authorization: Bearer {raw_key}" '
              f'-H "Content-Type: application/json" -d \'{{"prompt":"hello"}}\'')
        print()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
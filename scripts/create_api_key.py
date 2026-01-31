#!/usr/bin/env python3
"""
Create an API key and print it once. Store the key securely; it cannot be retrieved later.

Usage:
    DATABASE_URL=postgresql+asyncpg://... python scripts/create_api_key.py [--name "My key"]
"""
import argparse
import asyncio
import hashlib
import secrets
import sys

# Add project root to path so app is importable
sys.path.insert(0, "")

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_database_url
from app.models.api_key import ApiKey


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def main(name: str | None) -> None:
    url = get_database_url()
    engine = create_async_engine(url, echo=False)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, autocommit=False, autoflush=False
    )

    plain_key = secrets.token_urlsafe(32)
    key_hash = _hash_key(plain_key)

    async with async_session() as session:
        session.add(ApiKey(key_hash=key_hash, name=name or None))
        await session.commit()

    await engine.dispose()

    print("API key created. Store it securely; it will not be shown again.")
    print(plain_key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an API key")
    parser.add_argument("--name", type=str, default=None, help="Optional label for the key")
    args = parser.parse_args()
    asyncio.run(main(args.name))

import hashlib
import json
import redis.asyncio as redis
import os
import asyncio

LOCK_TTL = 10

def build_cache_key(
    
        tenant_id: str, 
        model: str,
        prompt: str,
        params: dict,
):
    normalized = {
        "tenant_id": tenant_id,
        "model": model,
        "prompt": prompt,
        "params": params
    }

    payload = json.dumps(normalized, sort_keys=True)
    digest = hashlib.sha256(payload.encode()).hexdigest()

    return f"cache:{digest}"

    
redis_client = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))

DEFAULT_CACHE_TTL = 60*5

async def cache_get(key: str):
    return await redis_client.get(key)

async def cache_set(key: str, value: str, ttl: int = DEFAULT_CACHE_TTL):
    await redis_client.set(key, value, ex=ttl)

async def acquire_lock(lock_key: str) -> bool:
    return await redis_client.set(lock_key, "1", nx=True, ex=LOCK_TTL)

async def release_lock(lock_key: str):
    await redis_client.delete(lock_key)
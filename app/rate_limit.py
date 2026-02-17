import time
from fastapi import HTTPException, status
from app.redis import redis_client

DEFAULT_REQUESTS_PER_MIN = 10

async def check_rate_limit(tenant_id: str, api_key_id: str):
    """Check if the tenant has exceeded the rate limit for the given API key.
    """

    now = int(time.time())
    window = now // 60
    key = f"rl:{tenant_id}:{api_key_id}:{window}"

    count = await redis_client.incr(key)

    if count == 1:
        await redis_client.expire(key, 60)
    
    if count > DEFAULT_REQUESTS_PER_MIN:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )
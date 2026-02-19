from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import make_asgi_app

from app.db import db_ping, redis_ping
# from app.deps import get_current_api_key
from app.auth import require_api_key, AuthContext
from app.models.api_key import ApiKey
from app.rate_limit import check_rate_limit
from app.cache import build_cache_key, cache_get, cache_set, acquire_lock, release_lock
from app.metrics import (
    REQUEST_COUNT, 
    REQUEST_LATENCY, 
    CACHE_HITS, 
    CACHE_MISSES, 
    RATE_LIMIT_HITS, 
    ERROR_COUNT
)

import json
import asyncio
import time

app = FastAPI(
    title="AI Inference Gateway",
    version="0.1.0"
)
metrics_app = make_asgi_app()

app.mount("/metrics/", metrics_app)

class PredictRequest(BaseModel):
    prompt: str
    model: str = "dummy-model"
    temperature: float = 0.0
    max_tokens: int = 100
    cache_bypass: bool = False

class PredictResponse(BaseModel):
    output: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    db_ok = await db_ping()
    redis_ok = await redis_ping()
    ready = db_ok and redis_ok
    return {"status": "ready" if ready else "not ready", "db": db_ok, "redis": redis_ok}

@app.post("/v1/predict", response_model=PredictResponse)
async def predict(
    req: PredictRequest,
    auth: AuthContext = Depends(require_api_key),
):
    tenant = str(auth.tenant_id)
    start_time = time.time()

    ###############################
    try:    
        # rate limiter will raise HTTPException with status code 429 if limit is exceeded
        await check_rate_limit(str(auth.tenant_id), str(auth.api_key_id))

        params = {
            "temperature": req.temperature,
            "max_tokens": req.max_tokens
        }

        cache_key = build_cache_key(
            tenant_id = str(auth.tenant_id),
            model = req.model,
            prompt = req.prompt,
            params = params
        )

        # read through cache unless cache_bypass is True
        if not req.cache_bypass:
            cached = await cache_get(cache_key)
            if cached:
                CACHE_HITS.labels(tenant_id=tenant).inc()
                REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
                REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
                data = json.loads(cached)
                return PredictResponse(**data)
            
            CACHE_MISSES.labels(tenant_id=tenant).inc()

            # acquire a lock to prevent thundering herd on cache miss
            acquired = await acquire_lock(f"lock:{cache_key}")

            if not acquired:
                # Another request is processing the same input, wait for it to finish
                for _ in range(20):
                    await asyncio.sleep(0.1)
                    cached = await cache_get(cache_key)
                    if cached:
                        CACHE_HITS.labels(tenant_id=tenant).inc()
                        REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
                        REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
                        data = json.loads(cached)
                        return PredictResponse(**data)
                # Timeout waiting for lock, proceed without cache
                output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
                REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
                REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
                return PredictResponse(output=output)
            
            # lock acquired, generate response and populate cache
            try:
                output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
                response_payload = json.dumps({"output": output})
                await cache_set(cache_key, response_payload)
                REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
                REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
                return PredictResponse(output=output)
                # return PredictResponse(output=f"[tenant={auth.tenant_id}] echo: {req.prompt}")
            finally:
                await release_lock(f"lock:{cache_key}")
        
        # cache bypass, directly generate response
        output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
        REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
        REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)

        return PredictResponse(output=output)

    except HTTPException as e:
        if e.status_code == 429:
            RATE_LIMIT_HITS.labels(tenant_id=tenant).inc()
        REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
        ERROR_COUNT.labels(tenant_id=tenant, error_type=str(e.status_code)).inc()
        raise   

    except Exception as e:
        REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
        ERROR_COUNT.labels(tenant_id=tenant, error_type="internal").inc()
        raise
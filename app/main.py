from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
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
    ERROR_COUNT,
    PROVIDER_FAILURES
)
from app.backends.router import BackendRouter
from app.logging_config import configure_logging


import json
import asyncio
import time
import structlog
import uuid

app = FastAPI(
    title="AI Inference Gateway",
    version="0.1.8" # 0.1.8 Structured logging, 0.1.7 Backend router, 0.1.6 Metrics and monitoring, 0.1.5 Cache locking, 0.1.4 Cache bypass, 0.1.3 Rate limiting, 0.1.2 Health checks, 0.1.1 API key auth, 0.1.0 Initial version
)

metrics_app = make_asgi_app()

# initialize backend
router = BackendRouter()
# configure logging
configure_logging()
logger = structlog.get_logger()
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

    # Route to backend
    backend, breaker, provider = router.get_backend_for_model(req.model)
    backend_name = backend.__class__.__name__

    try:
        # 1️⃣ Rate limit check
        await check_rate_limit(tenant, str(auth.api_key_id))

        # 2️⃣ Build cache key
        params = {
            "temperature": req.temperature,
            "max_tokens": req.max_tokens
        }

        cache_key = build_cache_key(
            tenant_id=tenant,
            model=req.model,
            prompt=req.prompt,
            params=params
        )

        # 3️⃣ Try cache first
        if not req.cache_bypass:
            cached = await cache_get(cache_key)
            if cached:
                CACHE_HITS.labels(tenant_id=tenant).inc()
                response_data = json.loads(cached)

                _record_success_metrics(tenant, start_time)
                logger.info(
                    "inference_success_cache",
                    tenant_id=tenant,
                    model=req.model,
                    backend=backend_name,
                )

                return PredictResponse(**response_data)

            CACHE_MISSES.labels(tenant_id=tenant).inc()

            # Prevent thundering herd
            output = await _run_with_lock(
                cache_key=cache_key,
                backend=backend,
                req=req,
                tenant=tenant,
                backend_name=backend_name
            )

        else:
            # 4️⃣ Direct inference (cache bypass)
            output = await backend.predict(
                prompt=req.prompt,
                model=req.model,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            )

        # 5️⃣ Success path
        _record_success_metrics(tenant, start_time)

        logger.info(
            "inference_success",
            tenant_id=tenant,
            model=req.model,
            backend=backend_name,
        )

        return PredictResponse(output=output)

    except HTTPException as e:
        if e.status_code == 429:
            RATE_LIMIT_HITS.labels(tenant_id=tenant).inc()

        REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
        ERROR_COUNT.labels(
            tenant_id=tenant,
            error_type=str(e.status_code)
        ).inc()

        logger.error(
            "inference_error",
            tenant_id=tenant,
            model=req.model,
            error=str(e),
        )
        raise

    except Exception as e:
        REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
        PROVIDER_FAILURES.labels(provider=provider).inc()
        ERROR_COUNT.labels(
            tenant_id=tenant,
            error_type="internal"
        ).inc()

        logger.exception(
            "inference_internal_error",
            tenant_id=tenant,
            model=req.model,
        )
        raise

async def _run_with_lock(
    cache_key: str,
    backend,
    req: PredictRequest,
    tenant: str,
    backend_name: str,
):
    lock_key = f"lock:{cache_key}"
    acquired = await acquire_lock(lock_key)

    if not acquired:
        # Wait for other request to populate cache
        for _ in range(20):
            await asyncio.sleep(0.1)
            cached = await cache_get(cache_key)
            if cached:
                CACHE_HITS.labels(tenant_id=tenant).inc()
                return json.loads(cached)["output"]

        # Fallback: no cache populated
        return await backend.predict(
            prompt=req.prompt,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

    try:
        output = await backend.predict(
            prompt=req.prompt,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        response_payload = json.dumps({"output": output})
        await cache_set(cache_key, response_payload)

        return output

    finally:
        await release_lock(lock_key)

def _record_success_metrics(tenant: str, start_time: float):
    REQUEST_COUNT.labels(
        tenant_id=tenant,
        status="success"
    ).inc()

    REQUEST_LATENCY.labels(
        tenant_id=tenant
    ).observe(time.time() - start_time)

# @app.post("/v1/predict", response_model=PredictResponse)
# async def predict(
#     req: PredictRequest,
#     auth: AuthContext = Depends(require_api_key),
# ):
#     tenant = str(auth.tenant_id)
#     start_time = time.time()
#     # use router to get the appropriate backend for the requested model
#     backend, breaker, provider = router.get_backend_for_model(req.model)
#     backend_name = backend.__class__.__name__

#     ###############################
#     try:    
#         # rate limiter will raise HTTPException with status code 429 if limit is exceeded
#         await check_rate_limit(str(auth.tenant_id), str(auth.api_key_id))

#         params = {
#             "temperature": req.temperature,
#             "max_tokens": req.max_tokens
#         }

#         cache_key = build_cache_key(
#             tenant_id = str(auth.tenant_id),
#             model = req.model,
#             prompt = req.prompt,
#             params = params
#         )

#         # read through cache unless cache_bypass is True
#         if not req.cache_bypass:
#             cached = await cache_get(cache_key)
#             if cached:
#                 CACHE_HITS.labels(tenant_id=tenant).inc()
#                 REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
#                 REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
#                 data = json.loads(cached)
#                 logger.info(
#                     "inference_success_cache",
#                     tenant_id=tenant,
#                     model=req.model,
#                     backend=backend_name,
#                     latency_ms = round((time.time() - start_time)*1000, 2),
#                 )
#                 return PredictResponse(**data)
            
#             CACHE_MISSES.labels(tenant_id=tenant).inc()

#             # acquire a lock to prevent thundering herd on cache miss
#             acquired = await acquire_lock(f"lock:{cache_key}")

#             if not acquired:
#                 # Another request is processing the same input, wait for it to finish
#                 for _ in range(20):
#                     await asyncio.sleep(0.1)
#                     cached = await cache_get(cache_key)
#                     if cached:
#                         CACHE_HITS.labels(tenant_id=tenant).inc()
#                         REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
#                         REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
#                         data = json.loads(cached)
#                         logger.info(
#                             "inference_success_cache",
#                             tenant_id=tenant,
#                             model=req.model,
#                             backend=backend_name,
#                             latency_ms = round((time.time() - start_time)*1000, 2),
#                         )
#                         return PredictResponse(**data)
#                 # Timeout waiting for lock, proceed without cache
#                 # output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
#                 output = await backend.predict(
#                     prompt=req.prompt,
#                     model=req.model,
#                     temperature=req.temperature,
#                     max_tokens=req.max_tokens
#                 )
#                 REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
#                 REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
#                 logger.info(
#                     "inference_success",
#                     tenant_id=tenant,
#                     model=req.model,
#                     backend=backend_name,
#                     latency_ms = round((time.time() - start_time)*1000, 2),
#                 )
#                 return PredictResponse(output=output)
            
#             # lock acquired, generate response and populate cache
#             try:
#                 # output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
#                 output = await backend.predict(
#                     prompt=req.prompt,
#                     model=req.model,
#                     temperature=req.temperature,
#                     max_tokens=req.max_tokens
#                 )

#                 response_payload = json.dumps({"output": output})
#                 await cache_set(cache_key, response_payload)
#                 REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
#                 REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)
#                 logger.info(
#                     "inference_success",
#                     tenant_id=tenant,
#                     model=req.model,
#                     backend=backend_name,
#                     latency_ms = round((time.time() - start_time)*1000, 2),
#                 )
#                 return PredictResponse(output=output)
#                 # return PredictResponse(output=f"[tenant={auth.tenant_id}] echo: {req.prompt}")
#             finally:
#                 await release_lock(f"lock:{cache_key}")
        
#         # cache bypass, directly generate response
#         # output = f"[tenant={auth.tenant_id}] echo: {req.prompt}"
#         output = await backend.predict(
#                     prompt=req.prompt,
#                     model=req.model,
#                     temperature=req.temperature,
#                     max_tokens=req.max_tokens
#                 )
#         logger.info(
#             "inference_success",
#             tenant_id=tenant,
#             model=req.model,
#             backend=backend_name,
#             latency_ms = round((time.time() - start_time)*1000, 2),
#         )
#         REQUEST_COUNT.labels(tenant_id=tenant, status="success").inc()
#         REQUEST_LATENCY.labels(tenant_id=tenant).observe(time.time() - start_time)

#         return PredictResponse(output=output)

#     except HTTPException as e:
#         if e.status_code == 429:
#             RATE_LIMIT_HITS.labels(tenant_id=tenant).inc()
#         REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
#         ERROR_COUNT.labels(tenant_id=tenant, error_type=str(e.status_code)).inc()
#         logger.error(
#             "inference_error",
#             tenant_id=tenant,
#             model=req.model,
#             error_type=str(e),
#         )
#         raise   

#     except Exception as e:
#         REQUEST_COUNT.labels(tenant_id=tenant, status="error").inc()
#         ERROR_COUNT.labels(tenant_id=tenant, error_type="internal").inc()
#         logger.error(
#             "inference_error",
#             tenant_id=tenant,
#             model=req.model,
#             error_type=str(e),
#         )
#         raise

## middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()

    response = None

    try: 
        response = await call_next(request)
        return response
    finally:
        latency = time.time() - start_time

        logger.info(
            "http_request",
            request_id=request_id,
            method = request.method,
            path = request.url.path,
            status_code = response.status_code if response else 500,
            latency_ms = round(latency*1000, 2),
        )

        if response and response.status_code >= 500:
            ERROR_COUNT.labels(tenant_id="unknown", error_type="server").inc()
        if response:
            response.headers["X-Request-ID"] = request_id
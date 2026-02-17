from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.db import db_ping, redis_ping
# from app.deps import get_current_api_key
from app.auth import require_api_key, AuthContext
from app.models.api_key import ApiKey
from app.rate_limit import check_rate_limit
from app.cache import build_cache_key, cache_get, cache_set

import json

app = FastAPI(
    title="AI Inference Gateway",
    version="0.1.0"
)

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
    redids_ok = await redis_ping()
    ready = db_ok and redids_ok
    return {"status": "ready" if ready else "not ready", "db": db_ok, "redis": redids_ok}

@app.post("/v1/predict", response_model=PredictResponse)
async def predict(
    req: PredictRequest,
    auth: AuthContext = Depends(require_api_key),
):
    
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

    if not req.cache_bypass:
        cached = await cache_get(cache_key)
        if cached:
            data = json.loads(cached)
            return PredictResponse(**data)

        await cache_set(cache_key, json.dumps({"output": f"[tenant={auth.tenant_id}] echo: {req.prompt}"}))

    return PredictResponse(output=f"[tenant={auth.tenant_id}] echo: {req.prompt}")


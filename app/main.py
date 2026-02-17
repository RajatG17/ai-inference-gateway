from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.db import db_ping, redis_ping
# from app.deps import get_current_api_key
from app.auth import require_api_key, AuthContext
from app.models.api_key import ApiKey
from app.rate_limit import check_rate_limit

app = FastAPI(
    title="AI Inference Gateway",
    version="0.1.0"
)

class PredictRequest(BaseModel):
    prompt: str

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
    return PredictResponse(output=f"[tenant={auth.tenant_id}] echo: {req.prompt}")


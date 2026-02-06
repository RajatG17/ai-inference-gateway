from typing import Annotated

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.db import db_ping
from app.deps import get_current_api_key
from app.models.api_key import ApiKey

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
    ok = await db_ping()
    return {"status": "ready"}

@app.post("/v1/predict", response_model=PredictResponse)
def predict(
    req: PredictRequest,
    _api_key: Annotated[ApiKey, Depends(get_current_api_key)],
):
    return PredictResponse(output=f"echo: {req.prompt}")


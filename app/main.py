from fastapi import FastAPI
from pydantic import BaseModel

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
def readyz():
    return {"status": "ready"}

@app.post("/v1/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    return PredictResponse(output=f"echo: {req.prompt}")


import hashlib
import os
import time
import pandas as pd
from fastapi import APIRouter, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.schemas import ClientFeatures, PredictionResponse
from app import model as model_state
from app.logger import log_prediction
from src.preprocessing import feature_engineering

router = APIRouter()

THRESHOLD = 0.5
_API_KEY_HASH = hashlib.sha256(os.getenv("API_KEY", "").encode()).hexdigest()
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _verify_api_key(api_key: str = Security(_api_key_header)):
    if not api_key or hashlib.sha256(api_key.encode()).hexdigest() != _API_KEY_HASH:
        raise HTTPException(status_code=403, detail="Non autorisé")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
def predict(features: ClientFeatures, _: None = Security(_verify_api_key)):
    if model_state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    data = pd.DataFrame([features.model_dump()])
    data = feature_engineering(data)
    t0 = time.perf_counter()
    score = float(model_state.model.predict(data)[0][1])
    inference_time_ms = (time.perf_counter() - t0) * 1000
    decision = "rejected" if score >= THRESHOLD else "approved"
    log_prediction(features, score, decision, inference_time_ms)
    return PredictionResponse(score=score, decision=decision)

import pandas as pd
from fastapi import APIRouter, HTTPException
from app.schemas import ClientFeatures, PredictionResponse
from app import model as model_state
from src.preprocessing import feature_engineering

router = APIRouter()

THRESHOLD = 0.5


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
def predict(features: ClientFeatures):
    if model_state.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    data = pd.DataFrame([features.model_dump()])
    data = feature_engineering(data)
    score = float(model_state.model.predict(data)[0][1])
    decision = "rejected" if score >= THRESHOLD else "approved"
    return PredictionResponse(score=score, decision=decision)

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app import model as model_state
from app.routes import router

MODEL_PATH = os.getenv("MODEL_PATH", "model")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_state.load(MODEL_PATH)
    yield


app = FastAPI(
    title="Credit Scoring API",
    description="Prédit la probabilité de défaut de paiement d'un client.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

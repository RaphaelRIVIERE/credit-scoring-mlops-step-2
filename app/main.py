import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
from app import model as model_state
from app.logger import init_db
from app.routes import router

MODEL_PATH = os.getenv("MODEL_PATH", "model")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_state.load(MODEL_PATH)
    init_db()
    yield


app = FastAPI(
    title="Credit Scoring API",
    description="Prédit la probabilité de défaut de paiement d'un client.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

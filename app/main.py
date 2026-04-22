import os
import time
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()
from app import model as model_state
from app.database import init_db
from app.logger import log_request
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


_EXCLUDED_PATHS = {"/", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    if request.url.path in _EXCLUDED_PATHS:
        return await call_next(request)
    t0 = time.perf_counter()
    error: str | None = None
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        error = str(e)
        raise
    finally:
        response_time_ms = (time.perf_counter() - t0) * 1000
        log_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error=error,
            prediction_id=getattr(request.state, "prediction_id", None),
        )
    return response


app.include_router(router)

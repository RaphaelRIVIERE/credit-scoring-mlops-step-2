import logging
import os
from typing import cast

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Log, Prediction
from app.schemas import ClientFeatures

logger = logging.getLogger(__name__)


def _get_engine():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is not set")
    return create_engine(url)


def init_db() -> None:
    try:
        Base.metadata.create_all(_get_engine())
    except Exception:
        logger.exception("Failed to initialize database")


def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    error: str | None = None,
    prediction_id: int | None = None,
) -> None:
    try:
        with Session(_get_engine()) as session:
            session.add(Log(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                error=error,
                prediction_id=prediction_id,
            ))
            session.commit()
    except Exception:
        logger.exception("Failed to log request")


def log_prediction(features: ClientFeatures, score: float, decision: str, inference_time_ms: float) -> int | None:
    try:
        with Session(_get_engine()) as session:
            prediction = Prediction(
                **features.model_dump(),
                score=score,
                decision=decision,
                inference_time_ms=inference_time_ms,
            )
            session.add(prediction)
            session.commit()
            session.refresh(prediction)
            return cast(int, prediction.id)
    except Exception:
        logger.exception("Failed to log prediction")
        return None

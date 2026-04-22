import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Prediction
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


def log_prediction(features: ClientFeatures, score: float, decision: str, inference_time_ms: float) -> None:
    try:
        with Session(_get_engine()) as session:
            session.add(Prediction(
                **features.model_dump(),
                score=score,
                decision=decision,
                inference_time_ms=inference_time_ms,
            ))
            session.commit()
    except Exception:
        logger.exception("Failed to log prediction")

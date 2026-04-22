import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.models import Base

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is not set")
    return create_engine(url)


def init_db() -> None:
    try:
        Base.metadata.create_all(get_engine())
    except Exception:
        logger.exception("Failed to initialize database")

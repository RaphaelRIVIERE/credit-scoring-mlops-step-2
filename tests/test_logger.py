import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Log, Prediction
from app.logger import log_prediction, log_request
from app.schemas import ClientFeatures

VALID_FEATURES = ClientFeatures(
    DAYS_BIRTH=-10000,
    DAYS_EMPLOYED=-3000,
    AMT_INCOME_TOTAL=150000,
    AMT_CREDIT=500000,
    AMT_ANNUITY=25000,
)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def mock_engine(engine):
    with patch("app.logger.get_engine", return_value=engine):
        yield


def test_log_prediction_inserts_row(engine):
    log_prediction(VALID_FEATURES, score=0.3, decision="approved", inference_time_ms=12.5)
    with Session(engine) as session:
        row = session.query(Prediction).first()
    assert row is not None
    assert row.score == pytest.approx(0.3)
    assert row.decision == "approved"
    assert row.DAYS_BIRTH == -10000
    assert row.AMT_INCOME_TOTAL == 150000


def test_log_request_inserts_row(engine):
    log_request(endpoint="/health", method="GET", status_code=200, response_time_ms=5.0)
    with Session(engine) as session:
        row = session.query(Log).first()
    assert row is not None
    assert row.endpoint == "/health"
    assert row.status_code == 200
    assert row.prediction_id is None


def test_log_request_with_prediction_id(engine):
    prediction_id = log_prediction(VALID_FEATURES, score=0.7, decision="rejected", inference_time_ms=10.0)
    log_request(endpoint="/predict", method="POST", status_code=200, response_time_ms=50.0, prediction_id=prediction_id)
    with Session(engine) as session:
        row = session.query(Log).first()
    assert row.prediction_id == prediction_id


def test_log_request_with_error(engine):
    log_request(endpoint="/predict", method="POST", status_code=500, response_time_ms=5.0, error="Model not loaded")
    with Session(engine) as session:
        row = session.query(Log).first()
    assert row.error == "Model not loaded"
    assert row.status_code == 500

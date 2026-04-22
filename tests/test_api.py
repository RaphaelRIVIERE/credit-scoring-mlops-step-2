import hashlib
import pytest
import app.model as model_state
import app.routes as routes_module
from app.main import app
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.models import Base

VALID_PAYLOAD = {
    "DAYS_BIRTH": -10000,
    "DAYS_EMPLOYED": -3000,
    "AMT_INCOME_TOTAL": 150000,
    "AMT_CREDIT": 500000,
    "AMT_ANNUITY": 25000,
}

API_KEY = "test-secret-key"


@pytest.fixture
def client():
    mock_model = MagicMock()
    mock_model.predict.return_value = [[0.7, 0.3]]

    def fake_load(_):
        model_state.model = mock_model

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)

    api_key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()
    with patch.object(model_state, "load", fake_load):
        with patch.object(routes_module, "_API_KEY_HASH", api_key_hash):
            with patch("app.logger.get_engine", return_value=test_engine):
                with TestClient(app) as c:
                    yield c

    Base.metadata.drop_all(test_engine)


def test_predict_valid(client):
    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == pytest.approx(0.3)
    assert data["decision"] == "approved"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_wrong_type(client):
    payload = {**VALID_PAYLOAD, "AMT_INCOME_TOTAL": "pas-un-nombre"}
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_invalid_days_birth(client):
    payload = {**VALID_PAYLOAD, "DAYS_BIRTH": 100}  # doit être < 0
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_invalid_income(client):
    payload = {**VALID_PAYLOAD, "AMT_INCOME_TOTAL": -5000}  # doit être > 0
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_missing_field(client):
    payload = VALID_PAYLOAD.copy()
    del payload["DAYS_BIRTH"]
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_no_api_key(client):
    response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 403


def test_predict_wrong_api_key(client):
    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": "mauvaise-cle"},
    )
    assert response.status_code == 403


def test_predict_model_not_loaded(client):
    with patch.object(model_state, "model", None):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        assert response.status_code == 503


def test_predict_invalid_amt_credit(client):
    payload = {**VALID_PAYLOAD, "AMT_CREDIT": -1000}
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_invalid_amt_annuity(client):
    payload = {**VALID_PAYLOAD, "AMT_ANNUITY": 0}
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 422


def test_predict_threshold_boundary_rejected(client):
    mock_model = MagicMock()  # score == 0.5 : la borne est inclusive, donc rejeté
    mock_model.predict.return_value = [[0.5, 0.5]]
    with patch.object(model_state, "model", mock_model):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == pytest.approx(0.5)
        assert data["decision"] == "rejected"


def test_predict_threshold_boundary_approved(client):
    mock_model = MagicMock()  # score juste sous 0.5 : approuvé
    mock_model.predict.return_value = [[0.5001, 0.4999]]
    with patch.object(model_state, "model", mock_model):
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == pytest.approx(0.4999)
        assert data["decision"] == "approved"



import hashlib
import pytest
import app.model as model_state
import app.routes as routes_module
from app.main import app
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

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
    model_state.model = mock_model

    api_key_hash = hashlib.sha256(API_KEY.encode()).hexdigest()
    with patch.object(routes_module, "_API_KEY_HASH", api_key_hash):
        with TestClient(app) as c:
            yield c


def test_predict_valid(client):
    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers={"X-API-Key": API_KEY},
    )
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["score"] <= 1
    assert data["decision"] in ("approved", "rejected")


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
    original = model_state.model
    model_state.model = None
    try:
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        assert response.status_code == 503
    finally:
        model_state.model = original


def test_predict_rejected(client):
    mock_model = MagicMock()
    mock_model.predict.return_value = [[0.3, 0.7]]
    original = model_state.model
    model_state.model = mock_model
    try:
        response = client.post(
            "/predict",
            json=VALID_PAYLOAD,
            headers={"X-API-Key": API_KEY},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == pytest.approx(0.7)
        assert data["decision"] == "rejected"
    finally:
        model_state.model = original

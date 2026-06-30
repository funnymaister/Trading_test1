from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

API_KEY = {"x-api-key": "change-me"}


def test_private_status_unauthorized():
    response = client.get("/status/private")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_private_status_authorized():
    response = client.get("/status/private", headers=API_KEY)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["access"] == "private"


def test_trade_execute_requires_api_key():
    payload = {
        "symbol": "BTC-USDT",
        "timeframe": "5m",
        "risk_percent": 1.0,
        "account_balance": 1000.0,
        "leverage": 5,
        "side": "buy",
        "order_type": "market",
        "idempotency_key": "secure-test-execute-1",
    }

    response = client.post("/trade/execute", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_trade_close_position_requires_api_key():
    payload = {
        "symbol": "BTC-USDT",
        "confirm_close": True,
    }

    response = client.post("/trade/close-position", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_scanner_refresh_requires_api_key():
    response = client.post("/scanner/top-movers/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"
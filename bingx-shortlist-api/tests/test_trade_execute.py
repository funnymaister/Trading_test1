from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


VALID_PAYLOAD = {
    "symbol": "BTC-USDT",
    "interval": "5m",
    "candles_limit": 200,
    "rr_target": 2.0,
    "account_balance": 1000,
    "risk_percent": 1.0,
    "leverage": 5,
    "confirm_live": True,
    "idempotency_key": "btc-5m-20260629-2300-001",
}


class DummySignalData:
    symbol = "BTC-USDT"
    interval = "5m"
    signal = "long"
    last_close = 65220.0
    ema_20 = 64990.1
    ema_50 = 64880.0
    rsi_14 = 58.4
    reason = "EMA20 > EMA50 and RSI confirms momentum"


class DummySignalResponse:
    data = DummySignalData()


async def mock_fetch_signal(query):
    return DummySignalResponse()


async def mock_build_execute_live_value_error(payload):
    raise ValueError("Live execution requires confirm_live=true")


async def mock_build_execute_live_conflict(payload):
    raise ValueError("Idempotency key already used with different payload")


async def mock_place_market_order(**kwargs):
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "orderId": "123456789",
        },
    }


def test_trade_execute_success_skeleton(monkeypatch):
    monkeypatch.setattr("services.trade_service.settings.enable_live_bingx", False)
    monkeypatch.setattr("services.trade_service.fetch_signal", mock_fetch_signal)
    monkeypatch.setattr("services.trade_service._EXECUTION_STORE", {})

    response = client.post("/trade/execute", json=VALID_PAYLOAD)

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["live_sent"] is False
    assert data["status"] == "accepted"
    assert data["idempotency_key"] == VALID_PAYLOAD["idempotency_key"]
    assert data["message"] == "Execution accepted in skeleton mode. No live order was sent."

    attempt = data["attempt"]
    assert attempt["symbol"] == "BTC-USDT"
    assert attempt["side"] == "buy"
    assert attempt["order_type"] == "market"
    assert attempt["quantity"] > 0
    assert attempt["leverage"] == 5
    assert attempt["entry_price"] == 65220.0
    assert attempt["stop_loss"] == 64880.0
    assert attempt["take_profit"] == 65900.0


def test_trade_execute_success_live(monkeypatch):
    monkeypatch.setattr("services.trade_service.settings.enable_live_bingx", True)
    monkeypatch.setattr("services.trade_service.fetch_signal", mock_fetch_signal)
    monkeypatch.setattr(
        "services.trade_service.bingx_execution_service.place_market_order",
        mock_place_market_order,
    )
    monkeypatch.setattr("services.trade_service._EXECUTION_STORE", {})

    live_payload = dict(VALID_PAYLOAD)
    live_payload["idempotency_key"] = "btc-5m-20260629-2300-002"

    response = client.post("/trade/execute", json=live_payload)

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["live_sent"] is True
    assert data["status"] == "accepted"
    assert data["idempotency_key"] == live_payload["idempotency_key"]
    assert data["message"] == "Live execution sent to BingX."

    attempt = data["attempt"]
    assert attempt["symbol"] == "BTC-USDT"
    assert attempt["side"] == "buy"
    assert attempt["order_type"] == "market"
    assert attempt["quantity"] > 0


def test_trade_execute_duplicate_same_payload(monkeypatch):
    monkeypatch.setattr("services.trade_service.settings.enable_live_bingx", False)
    monkeypatch.setattr("services.trade_service.fetch_signal", mock_fetch_signal)
    monkeypatch.setattr("services.trade_service._EXECUTION_STORE", {})

    first = client.post("/trade/execute", json=VALID_PAYLOAD)
    second = client.post("/trade/execute", json=VALID_PAYLOAD)

    assert first.status_code == 200
    assert second.status_code == 200

    second_data = second.json()
    assert second_data["live_sent"] is False
    assert second_data["status"] == "duplicate"
    assert second_data["idempotency_key"] == VALID_PAYLOAD["idempotency_key"]
    assert second_data["message"] == "Duplicate request detected. Previous execution attempt was reused."


def test_trade_execute_value_error(monkeypatch):
    monkeypatch.setattr("routers.trade.build_execute_live", mock_build_execute_live_value_error)

    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["confirm_live"] = False

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Live execution requires confirm_live=true"


def test_trade_execute_idempotency_conflict(monkeypatch):
    monkeypatch.setattr("routers.trade.build_execute_live", mock_build_execute_live_conflict)

    response = client.post("/trade/execute", json=VALID_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["detail"] == "Idempotency key already used with different payload"


def test_trade_execute_missing_confirm_live():
    bad_payload = dict(VALID_PAYLOAD)
    del bad_payload["confirm_live"]

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 422


def test_trade_execute_invalid_risk_percent():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["risk_percent"] = 5.0

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 422


def test_trade_execute_invalid_leverage():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["leverage"] = 50

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 422


def test_trade_execute_invalid_candles_limit():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["candles_limit"] = 10

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 422


def test_trade_execute_short_idempotency_key():
    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["idempotency_key"] = "short"

    response = client.post("/trade/execute", json=bad_payload)

    assert response.status_code == 422
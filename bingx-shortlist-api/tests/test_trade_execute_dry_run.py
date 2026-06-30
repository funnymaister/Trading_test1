from fastapi.testclient import TestClient

from main import app
from schemas.trade import TradePreviewQuery

client = TestClient(app)


MOCK_EXECUTE_DRY_RUN_RESPONSE = {
    "exchange": "BingX",
    "dry_run": True,
    "message": "Dry-run only. No live order was sent.",
    "order": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "order_type": "market",
        "quantity": 0.043497,
        "leverage": 5,
        "entry_price": 65220.0,
        "stop_loss": 64990.1,
        "take_profit": 65679.8,
        "reduce_only": False,
    },
}


async def mock_build_execute_dry_run(query):
    return MOCK_EXECUTE_DRY_RUN_RESPONSE


async def mock_build_execute_dry_run_error(query):
    raise ValueError("Invalid risk per unit for trade preview")


def test_trade_execute_dry_run_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_execute_dry_run", mock_build_execute_dry_run)

    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["dry_run"] is True
    assert data["message"] == "Dry-run only. No live order was sent."

    order = data["order"]
    assert order["symbol"] == "BTC-USDT"
    assert order["side"] == "buy"
    assert order["order_type"] == "market"
    assert order["quantity"] == 0.043497
    assert order["leverage"] == 5
    assert order["entry_price"] == 65220.0
    assert order["stop_loss"] == 64990.1
    assert order["take_profit"] == 65679.8
    assert order["reduce_only"] is False


def test_trade_execute_dry_run_value_error(monkeypatch):
    monkeypatch.setattr("routers.trade.build_execute_dry_run", mock_build_execute_dry_run_error)

    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid risk per unit for trade preview"


def test_trade_execute_dry_run_invalid_interval():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "2m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_execute_dry_run_invalid_candles_limit():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 10,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_execute_dry_run_invalid_rr_target():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 0.5,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_execute_dry_run_invalid_account_balance():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 5,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_execute_dry_run_invalid_risk_percent():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 10.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_execute_dry_run_invalid_leverage():
    response = client.get(
        "/trade/execute-dry-run",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000,
            "risk_percent": 1.0,
            "leverage": 100,
        },
    )

    assert response.status_code == 422

class TradeExecuteDryRunQuery(TradePreviewQuery):
        pass
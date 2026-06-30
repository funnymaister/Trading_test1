from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


MOCK_TRADE_PREVIEW_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "interval": "5m",
        "side": "buy",
        "signal": "long",
        "entry_type": "market",
        "entry_price": 65220.0,
        "stop_loss": 64990.1,
        "take_profit": 65679.8,
        "risk_reward_ratio": 2.0,
        "account_balance": 1000.0,
        "risk_percent": 1.0,
        "risk_amount_usdt": 10.0,
        "position_size_units": 0.043497,
        "position_notional_usdt": 2836.46,
        "required_margin_usdt": 567.292,
        "leverage": 5,
        "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
    },
}


async def mock_build_trade_preview(query):
    return MOCK_TRADE_PREVIEW_RESPONSE


async def mock_build_trade_preview_error(query):
    raise ValueError("Invalid risk per unit for trade preview")


def test_trade_preview_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview)

    response = client.get(
        "/trade/preview",
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

    preview = data["data"]
    assert preview["symbol"] == "BTC-USDT"
    assert preview["interval"] == "5m"
    assert preview["side"] == "buy"
    assert preview["signal"] == "long"
    assert preview["entry_type"] == "market"
    assert preview["entry_price"] == 65220.0
    assert preview["stop_loss"] == 64990.1
    assert preview["take_profit"] == 65679.8
    assert preview["risk_reward_ratio"] == 2.0
    assert preview["account_balance"] == 1000.0
    assert preview["risk_percent"] == 1.0
    assert preview["risk_amount_usdt"] == 10.0
    assert preview["position_size_units"] == 0.043497
    assert preview["position_notional_usdt"] == 2836.46
    assert preview["required_margin_usdt"] == 567.292
    assert preview["leverage"] == 5


def test_trade_preview_value_error(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview_error)

    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_interval():
    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_candles_limit():
    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_rr_target():
    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_account_balance():
    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_risk_percent():
    response = client.get(
        "/trade/preview",
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


def test_trade_preview_invalid_leverage():
    response = client.get(
        "/trade/preview",
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
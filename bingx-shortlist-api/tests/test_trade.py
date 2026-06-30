from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


MOCK_TRADE_PLAN_RESPONSE = {
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
        "risk_amount": 229.9,
        "reward_amount": 459.8,
        "risk_reward_ratio": 2.0,
        "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
    },
}


async def mock_build_trade_plan(query):
    return MOCK_TRADE_PLAN_RESPONSE


async def mock_build_trade_plan_error(query):
    raise ValueError("No actionable signal for trade plan")


def test_trade_plan_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan)

    response = client.get(
        "/trade/plan",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["interval"] == "5m"
    assert data["data"]["side"] == "buy"
    assert data["data"]["signal"] == "long"
    assert data["data"]["entry_type"] == "market"
    assert data["data"]["entry_price"] == 65220.0
    assert data["data"]["stop_loss"] == 64990.1
    assert data["data"]["take_profit"] == 65679.8
    assert data["data"]["risk_amount"] == 229.9
    assert data["data"]["reward_amount"] == 459.8
    assert data["data"]["risk_reward_ratio"] == 2.0


def test_trade_plan_no_actionable_signal(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan_error)

    response = client.get(
        "/trade/plan",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No actionable signal for trade plan"


def test_trade_plan_invalid_interval():
    response = client.get(
        "/trade/plan",
        params={
            "symbol": "BTC-USDT",
            "interval": "2m",
            "candles_limit": 200,
            "rr_target": 2.0,
        },
    )

    assert response.status_code == 422


def test_trade_plan_invalid_candles_limit():
    response = client.get(
        "/trade/plan",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 10,
            "rr_target": 2.0,
        },
    )

    assert response.status_code == 422


def test_trade_plan_invalid_rr_target():
    response = client.get(
        "/trade/plan",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 0.5,
        },
    )

    assert response.status_code == 422
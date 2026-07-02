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
        "position_notional_usdt": 2836.07,
        "required_margin_usdt": 567.21,
        "leverage": 5,
        "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
    },
}

MOCK_TRADE_DRY_RUN_RESPONSE = {
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

MOCK_TRADE_LIVE_RESPONSE = {
    "exchange": "BingX",
    "live_sent": False,
    "status": "accepted",
    "idempotency_key": "test-idem-123",
    "message": "Execution accepted in skeleton mode. No live order was sent.",
    "attempt": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "order_type": "market",
        "quantity": 0.043497,
        "leverage": 5,
        "entry_price": 65220.0,
        "stop_loss": 64990.1,
        "take_profit": 65679.8,
    },
    "exchange_response": None,
}


async def mock_build_trade_preview(query):
    return MOCK_TRADE_PREVIEW_RESPONSE


async def mock_build_trade_preview_error(query):
    raise ValueError("Invalid risk per unit for trade preview")


async def mock_build_execute_dry_run(query):
    return MOCK_TRADE_DRY_RUN_RESPONSE


async def mock_build_execute_live(query):
    return MOCK_TRADE_LIVE_RESPONSE


def test_trade_decision_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan)
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview)

    response = client.get(
        "/trade/decision",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["plan"]["symbol"] == "BTC-USDT"
    assert data["data"]["plan"]["interval"] == "5m"
    assert data["data"]["preview"]["symbol"] == "BTC-USDT"
    assert data["data"]["preview"]["leverage"] == 5
    assert data["data"]["preview"]["risk_amount_usdt"] == 10.0


def test_trade_decision_invalid(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan)
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview_error)

    response = client.get(
        "/trade/decision",
        params={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid risk per unit for trade preview"


def test_trade_decision_execute_dry_run_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan)
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview)
    monkeypatch.setattr("routers.trade.build_execute_dry_run", mock_build_execute_dry_run)

    response = client.post(
        "/trade/decision/execute",
        headers={"x-api-key": "test-internal-api-key"},
        json={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
            "idempotency_key": "test-idem-123",
            "confirm_live": False,
            "dry_run": True,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["mode"] == "dry_run"
    assert data["plan"]["symbol"] == "BTC-USDT"
    assert data["preview"]["symbol"] == "BTC-USDT"
    assert data["execution"]["dry_run"] is True
    assert data["execution"]["order"]["symbol"] == "BTC-USDT"


def test_trade_decision_execute_live_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_plan", mock_build_trade_plan)
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview)
    monkeypatch.setattr("routers.trade.build_execute_live", mock_build_execute_live)

    response = client.post(
        "/trade/decision/execute",
        headers={"x-api-key": "test-internal-api-key"},
        json={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
            "idempotency_key": "test-idem-123",
            "confirm_live": True,
            "dry_run": False,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["mode"] == "live"
    assert data["plan"]["symbol"] == "BTC-USDT"
    assert data["preview"]["symbol"] == "BTC-USDT"
    assert data["execution"]["status"] == "accepted"
    assert data["execution"]["idempotency_key"] == "test-idem-123"


def test_trade_decision_execute_validation_error():
    response = client.post(
        "/trade/decision/execute",
        headers={"x-api-key": "test-internal-api-key"},
        json={
            "symbol": "BTC-USDT",
            "interval": "2m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
            "idempotency_key": "test-idem-123",
            "confirm_live": False,
            "dry_run": True,
        },
    )

    assert response.status_code == 422


MOCK_TRADE_PREVIEW_ONLY_RESPONSE = {
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
        "position_notional_usdt": 2836.07,
        "required_margin_usdt": 567.21,
        "leverage": 5,
        "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
    },
}


async def mock_build_trade_preview_only(query):
    return MOCK_TRADE_PREVIEW_ONLY_RESPONSE


async def mock_build_trade_preview_only_error(query):
    raise ValueError("Invalid risk per unit for trade preview")


def test_trade_preview_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview_only)

    response = client.post(
        "/trade/preview",
        json={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["interval"] == "5m"
    assert data["data"]["leverage"] == 5
    assert data["data"]["risk_amount_usdt"] == 10.0
    assert data["data"]["position_size_units"] == 0.043497


def test_trade_preview_business_error(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_preview", mock_build_trade_preview_only_error)

    response = client.post(
        "/trade/preview",
        json={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid risk per unit for trade preview"


def test_trade_preview_invalid_interval():
    response = client.post(
        "/trade/preview",
        json={
            "symbol": "BTC-USDT",
            "interval": "2m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 1.0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


def test_trade_preview_invalid_risk_percent():
    response = client.post(
        "/trade/preview",
        json={
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_limit": 200,
            "rr_target": 2.0,
            "account_balance": 1000.0,
            "risk_percent": 0,
            "leverage": 5,
        },
    )

    assert response.status_code == 422


MOCK_TRAILING_STOP_PREVIEW_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "entry_price": 65220.0,
        "current_price": 65600.0,
        "current_stop_loss": 64990.1,
        "trail_distance_percent": 0.4,
        "activation_percent": 0.2,
        "activated": True,
        "proposed_stop_loss": 65337.6,
        "should_update": True,
        "reason": "Trailing stop activated and moved upward with favorable price action",
    },
}


async def mock_build_trailing_stop_preview(query):
    return MOCK_TRAILING_STOP_PREVIEW_RESPONSE


async def mock_build_trailing_stop_preview_error(query):
    raise ValueError("Trailing stop not activated yet")


def test_trailing_stop_preview_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_trailing_stop_preview",
        mock_build_trailing_stop_preview,
    )

    response = client.post(
        "/trade/trailing-stop/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65600.0,
            "current_stop_loss": 64990.1,
            "trail_distance_percent": 0.4,
            "activation_percent": 0.2,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["activated"] is True
    assert data["data"]["should_update"] is True
    assert data["data"]["proposed_stop_loss"] == 65337.6


def test_trailing_stop_preview_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_trailing_stop_preview",
        mock_build_trailing_stop_preview_error,
    )

    response = client.post(
        "/trade/trailing-stop/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65300.0,
            "current_stop_loss": 64990.1,
            "trail_distance_percent": 0.4,
            "activation_percent": 0.2,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Trailing stop not activated yet"


def test_trailing_stop_preview_invalid_side():
    response = client.post(
        "/trade/trailing-stop/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "entry_price": 65220.0,
            "current_price": 65600.0,
            "current_stop_loss": 64990.1,
            "trail_distance_percent": 0.4,
            "activation_percent": 0.2,
        },
    )

    assert response.status_code == 422


def test_trailing_stop_preview_invalid_trail_distance():
    response = client.post(
        "/trade/trailing-stop/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65600.0,
            "current_stop_loss": 64990.1,
            "trail_distance_percent": 0.0,
            "activation_percent": 0.2,
        },
    )

    assert response.status_code == 422


MOCK_PARTIAL_CLOSE_PREVIEW_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "position_size_units": 0.043497,
        "current_price": 65600.0,
        "close_percent": 50.0,
        "close_size_units": 0.021748,
        "remaining_size_units": 0.021749,
        "close_notional_usdt": 1426.67,
        "remaining_notional_usdt": 1426.74,
        "reason": "Partial close preview calculated from current position size and requested close percentage",
    },
}


async def mock_build_partial_close_preview(query):
    return MOCK_PARTIAL_CLOSE_PREVIEW_RESPONSE


async def mock_build_partial_close_preview_error(query):
    raise ValueError("Partial close amount is too small")


def test_partial_close_preview_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_partial_close_preview",
        mock_build_partial_close_preview,
    )

    response = client.post(
        "/trade/partial-close/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "position_size_units": 0.043497,
            "current_price": 65600.0,
            "close_percent": 50.0,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["close_percent"] == 50.0
    assert data["data"]["close_size_units"] == 0.021748
    assert data["data"]["remaining_size_units"] == 0.021749


def test_partial_close_preview_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_partial_close_preview",
        mock_build_partial_close_preview_error,
    )

    response = client.post(
        "/trade/partial-close/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "position_size_units": 0.043497,
            "current_price": 65600.0,
            "close_percent": 50.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Partial close amount is too small"


def test_partial_close_preview_invalid_side():
    response = client.post(
        "/trade/partial-close/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "position_size_units": 0.043497,
            "current_price": 65600.0,
            "close_percent": 50.0,
        },
    )

    assert response.status_code == 422


def test_partial_close_preview_invalid_close_percent():
    response = client.post(
        "/trade/partial-close/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "position_size_units": 0.043497,
            "current_price": 65600.0,
            "close_percent": 0.0,
        },
    )

    assert response.status_code == 422


MOCK_BREAKEVEN_PREVIEW_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "entry_price": 65220.0,
        "current_price": 65680.0,
        "current_stop_loss": 64990.1,
        "activation_rr": 1.0,
        "risk_per_unit": 229.9,
        "buffer_percent": 0.0,
        "activation_price": 65449.9,
        "activated": True,
        "proposed_stop_loss": 65220.0,
        "should_update": True,
        "reason": "Breakeven stop recalculated after activation threshold was reached",
    },
}


async def mock_build_breakeven_preview(query):
    return MOCK_BREAKEVEN_PREVIEW_RESPONSE


async def mock_build_breakeven_preview_error(query):
    raise ValueError("Breakeven not activated yet")


def test_breakeven_preview_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_breakeven_preview",
        mock_build_breakeven_preview,
    )

    response = client.post(
        "/trade/breakeven/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "buffer_percent": 0.0,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["activated"] is True
    assert data["data"]["proposed_stop_loss"] == 65220.0
    assert data["data"]["should_update"] is True


def test_breakeven_preview_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_breakeven_preview",
        mock_build_breakeven_preview_error,
    )

    response = client.post(
        "/trade/breakeven/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65300.0,
            "current_stop_loss": 64990.1,
            "activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "buffer_percent": 0.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Breakeven not activated yet"


def test_breakeven_preview_invalid_side():
    response = client.post(
        "/trade/breakeven/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "buffer_percent": 0.0,
        },
    )

    assert response.status_code == 422


def test_breakeven_preview_invalid_risk_per_unit():
    response = client.post(
        "/trade/breakeven/preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "activation_rr": 1.0,
            "risk_per_unit": 0.0,
            "buffer_percent": 0.0,
        },
    )

    assert response.status_code == 422
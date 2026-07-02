import asyncio
import json
import pytest
from pathlib import Path
from types import SimpleNamespace

from services.trade_service import (
    _load_trade_journal_entries,
    _save_trade_journal_entries,
    save_trade_journal_entry,
    get_trade_journal_entries,
    get_trade_journal_entry,
)

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


MOCK_POSITION_EXIT_PLAN_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "entry_price": 65220.0,
        "current_price": 65680.0,
        "current_stop_loss": 64990.1,
        "position_size_units": 0.043497,
        "partial_close": {
            "close_percent": 50.0,
            "close_size_units": 0.021748,
            "remaining_size_units": 0.021749,
            "close_notional_usdt": 1428.22,
        },
        "breakeven": {
            "activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "activation_price": 65449.9,
            "activated": True,
            "proposed_stop_loss": 65220.0,
        },
        "trailing_stop": {
            "activation_percent": 0.2,
            "distance_percent": 0.4,
            "activation_price": 65350.44,
            "activated": True,
            "proposed_stop_loss": 65417.28,
            "should_update": True,
        },
        "reason": "Combined exit plan generated with partial close, breakeven, and trailing stop logic",
    },
}


async def mock_build_position_exit_plan(query):
    return MOCK_POSITION_EXIT_PLAN_RESPONSE


async def mock_build_position_exit_plan_error(query):
    raise ValueError("Invalid trade side")


def test_position_exit_plan_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_position_exit_plan",
        mock_build_position_exit_plan,
    )

    response = client.post(
        "/trade/position-exit-plan",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "position_size_units": 0.043497,
            "partial_close_percent": 50.0,
            "breakeven_activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "trailing_activation_percent": 0.2,
            "trailing_distance_percent": 0.4,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["partial_close"]["close_percent"] == 50.0
    assert data["data"]["breakeven"]["activated"] is True
    assert data["data"]["trailing_stop"]["should_update"] is True


def test_position_exit_plan_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_position_exit_plan",
        mock_build_position_exit_plan_error,
    )

    response = client.post(
        "/trade/position-exit-plan",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "position_size_units": 0.043497,
            "partial_close_percent": 50.0,
            "breakeven_activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "trailing_activation_percent": 0.2,
            "trailing_distance_percent": 0.4,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid trade side"


def test_position_exit_plan_invalid_side():
    response = client.post(
        "/trade/position-exit-plan",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "position_size_units": 0.043497,
            "partial_close_percent": 50.0,
            "breakeven_activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "trailing_activation_percent": 0.2,
            "trailing_distance_percent": 0.4,
        },
    )

    assert response.status_code == 422


def test_position_exit_plan_invalid_partial_close_percent():
    response = client.post(
        "/trade/position-exit-plan",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "current_price": 65680.0,
            "current_stop_loss": 64990.1,
            "position_size_units": 0.043497,
            "partial_close_percent": 0.0,
            "breakeven_activation_rr": 1.0,
            "risk_per_unit": 229.9,
            "trailing_activation_percent": 0.2,
            "trailing_distance_percent": 0.4,
        },
    )

    assert response.status_code == 422


MOCK_TRADE_JOURNAL_PREVIEW_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "symbol": "BTC-USDT",
        "side": "buy",
        "entry_price": 65220.0,
        "stop_loss": 64990.1,
        "take_profit": 65679.8,
        "exit_price": 65550.0,
        "position_size_units": 0.043497,
        "fees_usdt": 2.5,
        "risk_per_unit": 229.9,
        "reward_per_unit": 459.8,
        "realized_per_unit": 330.0,
        "planned_rr": 2.0,
        "actual_rr": 1.4354,
        "r_multiple": 1.4354,
        "gross_pnl_usdt": 14.35,
        "net_pnl_usdt": 11.85,
        "outcome": "win",
        "note": "Closed early near resistance",
        "reason": "Trade journal preview calculated from planned trade levels and actual exit",
    },
}


async def mock_build_trade_journal_preview(query):
    return MOCK_TRADE_JOURNAL_PREVIEW_RESPONSE


async def mock_build_trade_journal_preview_error(query):
    raise ValueError("Invalid risk per unit for journal preview")


def test_trade_journal_preview_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_trade_journal_preview",
        mock_build_trade_journal_preview,
    )

    response = client.post(
        "/trade/journal-preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
            "note": "Closed early near resistance",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["planned_rr"] == 2.0
    assert data["data"]["actual_rr"] == 1.4354
    assert data["data"]["outcome"] == "win"


def test_trade_journal_preview_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.build_trade_journal_preview",
        mock_build_trade_journal_preview_error,
    )

    response = client.post(
        "/trade/journal-preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid risk per unit for journal preview"


def test_trade_journal_preview_invalid_side():
    response = client.post(
        "/trade/journal-preview",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
        },
    )

    assert response.status_code == 422


def test_trade_journal_preview_invalid_position_size():
    response = client.post(
        "/trade/journal-preview",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.0,
            "fees_usdt": 2.5,
        },
    )

    assert response.status_code == 422


MOCK_TRADE_STATS_RESPONSE = {
    "total_trades": 3,
    "win_rate_percent": 33.33,
    "loss_rate_percent": 33.33,
    "breakeven_rate_percent": 33.33,
    "avg_r_multiple": 0.5,
    "avg_win_r": 2.0,
    "avg_loss_r": -1.0,
    "expectancy_r": 0.3333,
    "total_net_pnl_usdt": 30.0,
    "avg_net_pnl_usdt": 10.0,
}


async def mock_build_trade_stats(query):
    return MOCK_TRADE_STATS_RESPONSE


def test_trade_stats_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_trade_stats", mock_build_trade_stats)

    response = client.post(
        "/trade/stats",
        json={
            "trades": [
                {"outcome": "win", "r_multiple": 2.0, "net_pnl_usdt": 40.0},
                {"outcome": "loss", "r_multiple": -1.0, "net_pnl_usdt": -20.0},
                {"outcome": "breakeven", "r_multiple": 0.0, "net_pnl_usdt": 10.0},
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total_trades"] == 3
    assert data["win_rate_percent"] == 33.33
    assert data["expectancy_r"] == 0.3333
    assert data["total_net_pnl_usdt"] == 30.0


def test_trade_stats_invalid_empty_trades():
    response = client.post(
        "/trade/stats",
        json={"trades": []},
    )

    assert response.status_code == 422

MOCK_TRADE_JOURNAL_SAVE_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "id": "journal-entry-123",
        "symbol": "BTC-USDT",
        "side": "buy",
        "outcome": "win",
        "entry_price": 65220.0,
        "stop_loss": 64990.1,
        "take_profit": 65679.8,
        "exit_price": 65550.0,
        "position_size_units": 0.043497,
        "fees_usdt": 2.5,
        "r_multiple": 1.4354,
        "net_pnl_usdt": 11.85,
        "note": "Closed early near resistance",
        "created_at": "2026-07-02T10:33:00+00:00",
    },
}


async def mock_save_trade_journal_entry(query):
    return MOCK_TRADE_JOURNAL_SAVE_RESPONSE


async def mock_save_trade_journal_entry_error(query):
    raise ValueError("Invalid trade side")


def test_trade_journal_save_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.save_trade_journal_entry",
        mock_save_trade_journal_entry,
    )

    response = client.post(
        "/trade/journal-save",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "outcome": "win",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
            "r_multiple": 1.4354,
            "net_pnl_usdt": 11.85,
            "note": "Closed early near resistance",
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["id"] == "journal-entry-123"
    assert data["data"]["symbol"] == "BTC-USDT"
    assert data["data"]["outcome"] == "win"
    assert data["data"]["r_multiple"] == 1.4354


def test_trade_journal_save_business_error(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.save_trade_journal_entry",
        mock_save_trade_journal_entry_error,
    )

    response = client.post(
        "/trade/journal-save",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "outcome": "win",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
            "r_multiple": 1.4354,
            "net_pnl_usdt": 11.85,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid trade side"


def test_trade_journal_save_invalid_side():
    response = client.post(
        "/trade/journal-save",
        json={
            "symbol": "BTC-USDT",
            "side": "long",
            "outcome": "win",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.043497,
            "fees_usdt": 2.5,
            "r_multiple": 1.4354,
            "net_pnl_usdt": 11.85,
        },
    )

    assert response.status_code == 422


def test_trade_journal_save_invalid_position_size():
    response = client.post(
        "/trade/journal-save",
        json={
            "symbol": "BTC-USDT",
            "side": "buy",
            "outcome": "win",
            "entry_price": 65220.0,
            "stop_loss": 64990.1,
            "take_profit": 65679.8,
            "exit_price": 65550.0,
            "position_size_units": 0.0,
            "fees_usdt": 2.5,
            "r_multiple": 1.4354,
            "net_pnl_usdt": 11.85,
        },
    )

    assert response.status_code == 422


def test_load_trade_journal_entries_returns_empty_when_file_missing(tmp_path):
    file_path = tmp_path / "trade_journal.json"

    entries = _load_trade_journal_entries(file_path)

    assert entries == []


def test_save_trade_journal_entries_writes_json_list(tmp_path):
    file_path = tmp_path / "trade_journal.json"
    entries = [{"id": "1", "symbol": "BTC-USDT"}]

    _save_trade_journal_entries(entries, file_path)

    assert file_path.exists()

    saved = json.loads(file_path.read_text(encoding="utf-8"))
    assert saved == entries


def test_save_trade_journal_entry_persists_entry(tmp_path, monkeypatch):
    test_file = tmp_path / "trade_journal.json"
    monkeypatch.setattr("services.trade_service.TRADE_JOURNAL_FILE", test_file)

    query = SimpleNamespace(
        symbol="BTC-USDT",
        side="buy",
        outcome="win",
        entry_price=65220.0,
        stop_loss=64990.1,
        take_profit=65679.8,
        exit_price=65550.0,
        position_size_units=0.043497,
        fees_usdt=2.5,
        r_multiple=1.4354,
        net_pnl_usdt=11.85,
        note="Closed early near resistance",
    )

    result = asyncio.run(save_trade_journal_entry(query))

    assert result["exchange"] == "BingX"
    assert result["data"]["symbol"] == "BTC-USDT"
    assert test_file.exists()

    saved = json.loads(test_file.read_text(encoding="utf-8"))
    assert len(saved) == 1
    assert saved[0]["symbol"] == "BTC-USDT"
    assert saved[0]["outcome"] == "win"


MOCK_TRADE_JOURNAL_LIST_RESPONSE = {
    "exchange": "BingX",
    "count": 2,
    "data": [
        {
            "id": "journal-entry-1",
            "symbol": "BTC-USDT",
            "side": "buy",
            "outcome": "win",
            "r_multiple": 1.5,
            "net_pnl_usdt": 12.4,
        },
        {
            "id": "journal-entry-2",
            "symbol": "ETH-USDT",
            "side": "sell",
            "outcome": "loss",
            "r_multiple": -1.0,
            "net_pnl_usdt": -8.0,
        },
    ],
}


MOCK_TRADE_JOURNAL_ENTRY_RESPONSE = {
    "exchange": "BingX",
    "data": {
        "id": "journal-entry-1",
        "symbol": "BTC-USDT",
        "side": "buy",
        "outcome": "win",
        "r_multiple": 1.5,
        "net_pnl_usdt": 12.4,
    },
}


async def mock_get_trade_journal_entries():
    return MOCK_TRADE_JOURNAL_LIST_RESPONSE


async def mock_get_trade_journal_entry(entry_id: str):
    return MOCK_TRADE_JOURNAL_ENTRY_RESPONSE


async def mock_get_trade_journal_entry_not_found(entry_id: str):
    raise ValueError("Trade journal entry not found")


def test_trade_journal_list_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.get_trade_journal_entries",
        mock_get_trade_journal_entries,
    )

    response = client.get("/trade/journal")

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["count"] == 2
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == "journal-entry-1"


def test_trade_journal_entry_success(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.get_trade_journal_entry",
        mock_get_trade_journal_entry,
    )

    response = client.get("/trade/journal/journal-entry-1")

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["data"]["id"] == "journal-entry-1"
    assert data["data"]["symbol"] == "BTC-USDT"


def test_trade_journal_entry_not_found(monkeypatch):
    monkeypatch.setattr(
        "routers.trade.get_trade_journal_entry",
        mock_get_trade_journal_entry_not_found,
    )

    response = client.get("/trade/journal/missing-entry")

    assert response.status_code == 404
    assert response.json()["detail"] == "Trade journal entry not found"

def test_get_trade_journal_entries_returns_saved_entries(tmp_path, monkeypatch):
    test_file = tmp_path / "trade_journal.json"
    entries = [
        {"id": "1", "symbol": "BTC-USDT"},
        {"id": "2", "symbol": "ETH-USDT"},
    ]
    test_file.write_text(json.dumps(entries), encoding="utf-8")

    monkeypatch.setattr("services.trade_service.TRADE_JOURNAL_FILE", test_file)

    result = asyncio.run(get_trade_journal_entries())

    assert result["exchange"] == "BingX"
    assert result["count"] == 2
    assert len(result["data"]) == 2


def test_get_trade_journal_entry_returns_matching_entry(tmp_path, monkeypatch):
    test_file = tmp_path / "trade_journal.json"
    entries = [
        {"id": "1", "symbol": "BTC-USDT"},
        {"id": "2", "symbol": "ETH-USDT"},
    ]
    test_file.write_text(json.dumps(entries), encoding="utf-8")

    monkeypatch.setattr("services.trade_service.TRADE_JOURNAL_FILE", test_file)

    result = asyncio.run(get_trade_journal_entry("2"))

    assert result["exchange"] == "BingX"
    assert result["data"]["id"] == "2"
    assert result["data"]["symbol"] == "ETH-USDT"

def test_get_trade_journal_entry_raises_when_missing(tmp_path, monkeypatch):
    test_file = tmp_path / "trade_journal.json"
    entries = [{"id": "1", "symbol": "BTC-USDT"}]
    test_file.write_text(json.dumps(entries), encoding="utf-8")

    monkeypatch.setattr("services.trade_service.TRADE_JOURNAL_FILE", test_file)

    with pytest.raises(ValueError, match="Trade journal entry not found"):
        asyncio.run(get_trade_journal_entry("999"))
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class DummyPositionsResponse:
    exchange = "BingX"
    items = [
        {
            "symbol": "BTC-USDT",
            "position_side": "BOTH",
            "side": "buy",
            "quantity": 0.015,
            "entry_price": 65000.0,
            "mark_price": 65220.0,
            "unrealized_pnl": 3.3,
            "liquidation_price": 58000.0,
            "leverage": 5,
        }
    ]


class DummyOpenOrdersResponse:
    exchange = "BingX"
    items = [
        {
            "order_id": "123456",
            "symbol": "BTC-USDT",
            "side": "SELL",
            "order_type": "LIMIT",
            "status": "NEW",
            "price": 66000.0,
            "quantity": 0.015,
        }
    ]


class DummyClosePositionResponse:
    exchange = "BingX"
    live_sent = False
    message = "Close position accepted in skeleton mode. No live order was sent."
    attempt = {
        "symbol": "BTC-USDT",
        "side": "sell",
        "order_type": "market",
        "quantity": 0.015,
        "position_side": "BOTH",
    }


async def mock_build_positions(symbol=None):
    return DummyPositionsResponse()


async def mock_build_open_orders(symbol=None):
    return DummyOpenOrdersResponse()


async def mock_build_close_position(payload):
    return DummyClosePositionResponse()


async def mock_build_close_position_error(payload):
    raise ValueError("Closing a position requires confirm_close=true")


def test_trade_positions_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_positions", mock_build_positions)

    response = client.get("/trade/positions")

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["symbol"] == "BTC-USDT"
    assert item["position_side"] == "BOTH"
    assert item["side"] == "buy"
    assert item["quantity"] == 0.015
    assert item["entry_price"] == 65000.0
    assert item["mark_price"] == 65220.0
    assert item["unrealized_pnl"] == 3.3
    assert item["liquidation_price"] == 58000.0
    assert item["leverage"] == 5


def test_trade_positions_success_with_symbol(monkeypatch):
    monkeypatch.setattr("routers.trade.build_positions", mock_build_positions)

    response = client.get("/trade/positions", params={"symbol": "BTC-USDT"})

    assert response.status_code == 200
    data = response.json()
    assert data["exchange"] == "BingX"
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "BTC-USDT"


def test_trade_open_orders_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_open_orders", mock_build_open_orders)

    response = client.get("/trade/open-orders")

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["order_id"] == "123456"
    assert item["symbol"] == "BTC-USDT"
    assert item["side"] == "SELL"
    assert item["order_type"] == "LIMIT"
    assert item["status"] == "NEW"
    assert item["price"] == 66000.0
    assert item["quantity"] == 0.015


def test_trade_open_orders_success_with_symbol(monkeypatch):
    monkeypatch.setattr("routers.trade.build_open_orders", mock_build_open_orders)

    response = client.get("/trade/open-orders", params={"symbol": "BTC-USDT"})

    assert response.status_code == 200
    data = response.json()
    assert data["exchange"] == "BingX"
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "BTC-USDT"


def test_trade_close_position_success(monkeypatch):
    monkeypatch.setattr("routers.trade.build_close_position", mock_build_close_position)

    payload = {
        "symbol": "BTC-USDT",
        "confirm_close": True,
    }

    response = client.post("/trade/close-position", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["live_sent"] is False
    assert data["message"] == "Close position accepted in skeleton mode. No live order was sent."

    attempt = data["attempt"]
    assert attempt["symbol"] == "BTC-USDT"
    assert attempt["side"] == "sell"
    assert attempt["order_type"] == "market"
    assert attempt["quantity"] == 0.015
    assert attempt["position_side"] == "BOTH"


def test_trade_close_position_value_error(monkeypatch):
    monkeypatch.setattr("routers.trade.build_close_position", mock_build_close_position_error)

    payload = {
        "symbol": "BTC-USDT",
        "confirm_close": False,
    }

    response = client.post("/trade/close-position", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Closing a position requires confirm_close=true"


def test_trade_close_position_missing_confirm_close():
    payload = {
        "symbol": "BTC-USDT",
    }

    response = client.post("/trade/close-position", json=payload)

    assert response.status_code == 422


def test_trade_close_position_invalid_symbol():
    payload = {
        "symbol": "BT",
        "confirm_close": True,
    }

    response = client.post("/trade/close-position", json=payload)

    assert response.status_code == 422
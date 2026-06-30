from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


async def mock_get_24h_tickers():
    return [
        {
            "symbol": "BTC-USDT",
            "priceChangePercent": "5.2",
            "lastPrice": "65220.0",
            "quoteVolume": "120000000",
        },
        {
            "symbol": "ETH-USDT",
            "priceChangePercent": "7.8",
            "lastPrice": "3550.0",
            "quoteVolume": "98000000",
        },
        {
            "symbol": "SOL-USDT",
            "priceChangePercent": "3.1",
            "lastPrice": "145.0",
            "quoteVolume": "54000000",
        },
        {
            "symbol": "DOGE-USDC",
            "priceChangePercent": "9.9",
            "lastPrice": "0.12",
            "quoteVolume": "111111",
        },
    ]


def test_scanner_refresh_success(monkeypatch):
    monkeypatch.setattr(
        "clients.bingx_market_client.bingx_market_client.get_24h_tickers",
        mock_get_24h_tickers,
    )

    response = client.post("/scanner/top-movers/refresh")

    assert response.status_code == 200
    data = response.json()

    assert data["exchange"] == "BingX"
    assert data["count"] == 3
    assert data["updated_at"] is not None
    assert len(data["items"]) == 3

    assert data["items"][0]["symbol"] == "ETH-USDT"
    assert data["items"][0]["price_change_percent"] == 7.8
    assert data["items"][1]["symbol"] == "BTC-USDT"
    assert data["items"][2]["symbol"] == "SOL-USDT"


def test_scanner_get_top_movers_after_refresh(monkeypatch):
    monkeypatch.setattr(
        "clients.bingx_market_client.bingx_market_client.get_24h_tickers",
        mock_get_24h_tickers,
    )

    refresh_response = client.post("/scanner/top-movers/refresh")
    assert refresh_response.status_code == 200

    response = client.get("/scanner/top-movers")
    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["count"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["symbol"] == "ETH-USDT"


def test_scanner_get_top_movers_empty_initial_state():
    response = client.get("/scanner/top-movers")

    assert response.status_code == 200
    data = response.json()

    assert data["exchange"] == "BingX"
    assert "count" in data
    assert "items" in data
    assert isinstance(data["items"], list)
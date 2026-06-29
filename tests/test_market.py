from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


MOCK_CONTRACTS = [
    {
        "symbol": "BTC-USDT",
        "status": 1,
        "quoteAsset": "USDT",
        "minNotional": "5",
        "tickSize": "0.1",
        "stepSize": "0.001",
        "apiStateBuy": True,
        "apiStateSell": True,
    },
    {
        "symbol": "ETH-USDT",
        "status": 1,
        "quoteAsset": "USDT",
        "minNotional": "10",
        "tickSize": "0.01",
        "stepSize": "0.001",
        "apiStateBuy": True,
        "apiStateSell": True,
    },
    {
        "symbol": "XRP-USDT",
        "status": 0,
        "quoteAsset": "USDT",
        "minNotional": "1",
        "tickSize": "0.0001",
        "stepSize": "1",
        "apiStateBuy": True,
        "apiStateSell": True,
    },
    {
        "symbol": "SOL-USDC",
        "status": 1,
        "quoteAsset": "USDC",
        "minNotional": "5",
        "tickSize": "0.01",
        "stepSize": "0.01",
        "apiStateBuy": True,
        "apiStateSell": True,
    },
    {
        "symbol": "DOGE-USDT",
        "status": 1,
        "quoteAsset": "USDT",
        "minNotional": "20",
        "tickSize": "0.0001",
        "stepSize": "1",
        "apiStateBuy": False,
        "apiStateSell": True,
    },
]


async def mock_fetch_contracts():
    return MOCK_CONTRACTS


def test_market_health():
    response = client.get("/market/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_market_shortlist_basic(monkeypatch):
    monkeypatch.setattr("routers.market.fetch_contracts", mock_fetch_contracts)

    response = client.get("/market/shortlist", params={"quote_asset": "USDT", "limit": 10})
    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["total_symbols"] == 5
    assert data["filtered_symbols"] == 2
    assert data["filters"]["quote_asset"] == "USDT"
    assert data["filters"]["limit"] == 10

    symbols = [item["symbol"] for item in data["items"]]
    assert symbols == ["BTC-USDT", "ETH-USDT"]


def test_market_shortlist_min_notional(monkeypatch):
    monkeypatch.setattr("routers.market.fetch_contracts", mock_fetch_contracts)

    response = client.get(
        "/market/shortlist",
        params={"quote_asset": "USDT", "limit": 10, "min_notional": 6},
    )
    assert response.status_code == 200

    data = response.json()
    symbols = [item["symbol"] for item in data["items"]]
    assert symbols == ["ETH-USDT"]


def test_market_shortlist_quote_asset(monkeypatch):
    monkeypatch.setattr("routers.market.fetch_contracts", mock_fetch_contracts)

    response = client.get("/market/shortlist", params={"quote_asset": "USDC", "limit": 10})
    assert response.status_code == 200

    data = response.json()
    symbols = [item["symbol"] for item in data["items"]]
    assert symbols == ["SOL-USDC"]


def test_market_shortlist_limit_validation():
    response = client.get("/market/shortlist", params={"limit": 0})
    assert response.status_code == 422
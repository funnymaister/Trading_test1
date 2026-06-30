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

    MOCK_TICKERS = [
        {
            "symbol": "BTC-USDT",
            "lastPrice": "100000",
            "priceChangePercent": "5.5",
            "highPrice": "101000",
            "lowPrice": "95000",
            "volume": "12345",
        },
        {
            "symbol": "ETH-USDT",
            "lastPrice": "3500",
            "priceChangePercent": "8.2",
            "highPrice": "3600",
            "lowPrice": "3200",
            "volume": "54321",
        },
        {
            "symbol": "XRP-USDT",
            "lastPrice": "0.60",
            "priceChangePercent": "-4.1",
            "highPrice": "0.64",
            "lowPrice": "0.58",
            "volume": "999999",
        },
        {
            "symbol": "SOL-USDC",
            "lastPrice": "180",
            "priceChangePercent": "12.7",
            "highPrice": "185",
            "lowPrice": "160",
            "volume": "77777",
        },
        {
            "symbol": "DOGE-USDT",
            "lastPrice": "0.18",
            "priceChangePercent": "-7.3",
            "highPrice": "0.20",
            "lowPrice": "0.17",
            "volume": "888888",
        },
    ]

    async def mock_fetch_tickers_24h():
        return MOCK_TICKERS

    def test_market_movers_gainers(monkeypatch):
        monkeypatch.setattr("routers.market.fetch_tickers_24h", mock_fetch_tickers_24h)

        response = client.get("/market/movers", params={"quote_asset": "USDT", "limit": 2, "sort": "gainers"})
        assert response.status_code == 200

        data = response.json()
        assert data["exchange"] == "BingX"
        assert data["filters"]["quote_asset"] == "USDT"
        assert data["filters"]["sort"] == "gainers"
        assert data["filtered_symbols"] == 2

        symbols = [item["symbol"] for item in data["items"]]
        assert symbols == ["ETH-USDT", "BTC-USDT"]

    def test_market_movers_quote_asset(monkeypatch):
        monkeypatch.setattr("routers.market.fetch_tickers_24h", mock_fetch_tickers_24h)

        response = client.get("/market/movers", params={"quote_asset": "USDC", "limit": 10, "sort": "gainers"})
        assert response.status_code == 200

        data = response.json()
        symbols = [item["symbol"] for item in data["items"]]
        assert symbols == ["SOL-USDC"]

    def test_market_movers_losers(monkeypatch):
        monkeypatch.setattr("routers.market.fetch_tickers_24h", mock_fetch_tickers_24h)

        response = client.get("/market/movers", params={"quote_asset": "USDT", "limit": 2, "sort": "losers"})
        assert response.status_code == 200

        data = response.json()
        symbols = [item["symbol"] for item in data["items"]]
        assert symbols == ["DOGE-USDT", "XRP-USDT"]


MOCK_CANDLES_RESPONSE = {
    "exchange": "BingX",
    "symbol": "BTC-USDT",
    "interval": "5m",
    "count": 3,
    "items": [
        {
            "open_time": 1710000000000,
            "open": 65000.0,
            "high": 65100.0,
            "low": 64950.0,
            "close": 65080.0,
            "volume": 123.45,
        },
        {
            "open_time": 1710000300000,
            "open": 65080.0,
            "high": 65200.0,
            "low": 65010.0,
            "close": 65150.0,
            "volume": 156.78,
        },
        {
            "open_time": 1710000600000,
            "open": 65150.0,
            "high": 65300.0,
            "low": 65100.0,
            "close": 65220.0,
            "volume": 111.22,
        },
    ],
}


async def mock_fetch_candles(query):
    return MOCK_CANDLES_RESPONSE


def test_market_candles_success(monkeypatch):
    monkeypatch.setattr("routers.market.fetch_candles", mock_fetch_candles)

    response = client.get(
        "/market/candles",
        params={"symbol": "BTC-USDT", "interval": "5m", "limit": 3},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["exchange"] == "BingX"
    assert data["symbol"] == "BTC-USDT"
    assert data["interval"] == "5m"
    assert data["count"] == 3
    assert len(data["items"]) == 3
    assert data["items"][0]["open"] == 65000.0
    assert data["items"][2]["close"] == 65220.0


def test_market_candles_validation_error():
    response = client.get(
        "/market/candles",
        params={"symbol": "BTC-USDT", "interval": "2m", "limit": 3},
    )

    assert response.status_code == 422

    MOCK_INDICATORS_RESPONSE = {
        "exchange": "BingX",
        "data": {
            "symbol": "BTC-USDT",
            "interval": "5m",
            "candles_count": 200,
            "last_close": 65220.0,
            "ema_20": 65180.25,
            "ema_50": 64990.10,
            "rsi_14": 58.44,
        },
    }

    async def mock_fetch_indicators(query):
        return MOCK_INDICATORS_RESPONSE

    def test_market_indicators_success(monkeypatch):
        monkeypatch.setattr("routers.market.fetch_indicators", mock_fetch_indicators)

        response = client.get(
            "/market/indicators",
            params={"symbol": "BTC-USDT", "interval": "5m", "limit": 200},
        )

        assert response.status_code == 200

        data = response.json()
        assert data["exchange"] == "BingX"
        assert data["data"]["symbol"] == "BTC-USDT"
        assert data["data"]["interval"] == "5m"
        assert data["data"]["candles_count"] == 200
        assert data["data"]["last_close"] == 65220.0
        assert data["data"]["ema_20"] == 65180.25
        assert data["data"]["ema_50"] == 64990.10
        assert data["data"]["rsi_14"] == 58.44

    def test_market_indicators_invalid_interval():
        response = client.get(
            "/market/indicators",
            params={"symbol": "BTC-USDT", "interval": "2m", "limit": 200},
        )

        assert response.status_code == 422

    def test_market_indicators_invalid_limit():
        response = client.get(
            "/market/indicators",
            params={"symbol": "BTC-USDT", "interval": "5m", "limit": 10},
        )

        assert response.status_code == 422

        MOCK_SIGNAL_RESPONSE = {
            "exchange": "BingX",
            "data": {
                "symbol": "BTC-USDT",
                "interval": "5m",
                "signal": "long",
                "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
                "candles_count": 200,
                "last_close": 65220.0,
                "ema_20": 65180.25,
                "ema_50": 64990.10,
                "rsi_14": 58.44,
            },
        }

        async def mock_fetch_signal(query):
            return MOCK_SIGNAL_RESPONSE

        def test_market_signals_success(monkeypatch):
            monkeypatch.setattr("routers.market.fetch_signal", mock_fetch_signal)

            response = client.get(
                "/market/signals",
                params={"symbol": "BTC-USDT", "interval": "5m", "limit": 200},
            )

            assert response.status_code == 200

            data = response.json()
            assert data["exchange"] == "BingX"
            assert data["data"]["symbol"] == "BTC-USDT"
            assert data["data"]["interval"] == "5m"
            assert data["data"]["signal"] == "long"
            assert "EMA20" in data["data"]["reason"]
            assert data["data"]["candles_count"] == 200
            assert data["data"]["last_close"] == 65220.0
            assert data["data"]["ema_20"] == 65180.25
            assert data["data"]["ema_50"] == 64990.10
            assert data["data"]["rsi_14"] == 58.44

        def test_market_signals_invalid_interval():
            response = client.get(
                "/market/signals",
                params={"symbol": "BTC-USDT", "interval": "2m", "limit": 200},
            )

            assert response.status_code == 422

        def test_market_signals_invalid_limit():
            response = client.get(
                "/market/signals",
                params={"symbol": "BTC-USDT", "interval": "5m", "limit": 10},
            )

            assert response.status_code == 422

            MOCK_SCANNER_RESPONSE = {
                "exchange": "BingX",
                "interval": "5m",
                "scanned": 3,
                "signals_found": 2,
                "items": [
                    {
                        "symbol": "BTC-USDT",
                        "interval": "5m",
                        "signal": "long",
                        "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
                        "candles_count": 200,
                        "last_close": 65220.0,
                        "ema_20": 65180.25,
                        "ema_50": 64990.10,
                        "rsi_14": 58.44,
                    },
                    {
                        "symbol": "ETH-USDT",
                        "interval": "5m",
                        "signal": "short",
                        "reason": "Price below EMA20 and EMA50, RSI confirms bearish momentum",
                        "candles_count": 200,
                        "last_close": 3480.5,
                        "ema_20": 3492.1,
                        "ema_50": 3510.8,
                        "rsi_14": 41.2,
                    },
                ],
            }

            async def mock_fetch_signal_scanner(query):
                return MOCK_SCANNER_RESPONSE

            def test_market_scanner_success(monkeypatch):
                monkeypatch.setattr("routers.market.fetch_signal_scanner", mock_fetch_signal_scanner)

                response = client.get(
                    "/market/scanner",
                    params={"interval": "5m", "limit": 3, "candles_limit": 200},
                )

                assert response.status_code == 200

                data = response.json()
                assert data["exchange"] == "BingX"
                assert data["interval"] == "5m"
                assert data["scanned"] == 3
                assert data["signals_found"] == 2
                assert len(data["items"]) == 2

                assert data["items"][0]["symbol"] == "BTC-USDT"
                assert data["items"][0]["signal"] == "long"

                assert data["items"][1]["symbol"] == "ETH-USDT"
                assert data["items"][1]["signal"] == "short"

            def test_market_scanner_invalid_interval():
                response = client.get(
                    "/market/scanner",
                    params={"interval": "2m", "limit": 3, "candles_limit": 200},
                )

                assert response.status_code == 422

            def test_market_scanner_invalid_limit():
                response = client.get(
                    "/market/scanner",
                    params={"interval": "5m", "limit": 25, "candles_limit": 200},
                )

                assert response.status_code == 422

            def test_market_scanner_invalid_candles_limit():
                response = client.get(
                    "/market/scanner",
                    params={"interval": "5m", "limit": 3, "candles_limit": 10},
                )

                assert response.status_code == 422

                MOCK_CANDIDATES_RESPONSE = {
                    "exchange": "BingX",
                    "interval": "5m",
                    "scanned": 5,
                    "candidates_found": 3,
                    "items": [
                        {
                            "symbol": "BTC-USDT",
                            "interval": "5m",
                            "signal": "long",
                            "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
                            "score": 7.8421,
                            "candles_count": 200,
                            "last_close": 65220.0,
                            "ema_20": 65180.25,
                            "ema_50": 64990.10,
                            "rsi_14": 58.44,
                        },
                        {
                            "symbol": "SOL-USDT",
                            "interval": "5m",
                            "signal": "long",
                            "reason": "Price above EMA20 and EMA50, RSI confirms bullish momentum",
                            "score": 6.1123,
                            "candles_count": 200,
                            "last_close": 172.8,
                            "ema_20": 171.9,
                            "ema_50": 169.7,
                            "rsi_14": 61.2,
                        },
                        {
                            "symbol": "ETH-USDT",
                            "interval": "5m",
                            "signal": "short",
                            "reason": "Price below EMA20 and EMA50, RSI confirms bearish momentum",
                            "score": 5.5501,
                            "candles_count": 200,
                            "last_close": 3480.5,
                            "ema_20": 3492.1,
                            "ema_50": 3510.8,
                            "rsi_14": 41.2,
                        },
                    ],
                }

                async def mock_fetch_candidates(query):
                    return MOCK_CANDIDATES_RESPONSE

                def test_market_candidates_success(monkeypatch):
                    monkeypatch.setattr("routers.market.fetch_candidates", mock_fetch_candidates)

                    response = client.get(
                        "/market/candidates",
                        params={"interval": "5m", "limit": 5, "candles_limit": 200, "top_k": 3},
                    )

                    assert response.status_code == 200

                    data = response.json()
                    assert data["exchange"] == "BingX"
                    assert data["interval"] == "5m"
                    assert data["scanned"] == 5
                    assert data["candidates_found"] == 3
                    assert len(data["items"]) == 3

                    assert data["items"][0]["symbol"] == "BTC-USDT"
                    assert data["items"][0]["score"] == 7.8421
                    assert data["items"][1]["symbol"] == "SOL-USDT"
                    assert data["items"][2]["symbol"] == "ETH-USDT"

                    assert data["items"][0]["score"] >= data["items"][1]["score"]
                    assert data["items"][1]["score"] >= data["items"][2]["score"]

                def test_market_candidates_invalid_interval():
                    response = client.get(
                        "/market/candidates",
                        params={"interval": "2m", "limit": 5, "candles_limit": 200, "top_k": 3},
                    )

                    assert response.status_code == 422

                def test_market_candidates_invalid_limit():
                    response = client.get(
                        "/market/candidates",
                        params={"interval": "5m", "limit": 25, "candles_limit": 200, "top_k": 3},
                    )

                    assert response.status_code == 422

                def test_market_candidates_invalid_candles_limit():
                    response = client.get(
                        "/market/candidates",
                        params={"interval": "5m", "limit": 5, "candles_limit": 10, "top_k": 3},
                    )

                    assert response.status_code == 422

                def test_market_candidates_invalid_top_k():
                    response = client.get(
                        "/market/candidates",
                        params={"interval": "5m", "limit": 5, "candles_limit": 200, "top_k": 25},
                    )

                    assert response.status_code == 422
from __future__ import annotations
from fastapi import HTTPException
from typing import Any

from schemas.market import (
    Candle,
    CandidateItem,
    CandidatesQuery,
    CandidatesResponse,
    CandlesQuery,
    CandlesResponse,
    IndicatorSnapshot,
    IndicatorsQuery,
    IndicatorsResponse,
    MarketMover,
    MarketSymbol,
    MoversQuery,
    MoversResponse,
    ScannerQuery,
    ScannerResponse,
    ShortlistQuery,
    ShortlistResponse,
    SignalQuery,
    SignalResponse,
    SignalSnapshot,
)

import httpx
import time
import logging
import asyncio

CONTRACTS_CACHE: list[dict[str, Any]] = []
CONTRACTS_CACHE_TS: float = 0.0

TICKERS_CACHE: list[dict[str, Any]] = []
TICKERS_CACHE_TS: float = 0.0

logger = logging.getLogger(__name__)

def _upstream_error(detail: str) -> HTTPException:
    return HTTPException(status_code=502, detail=detail)

from schemas.market import (
    MarketMover,
    MarketSymbol,
    MoversQuery,
    MoversResponse,
    ShortlistQuery,
    ShortlistResponse,
)

from config import settings
from schemas.market import MarketSymbol, ShortlistQuery, ShortlistResponse


async def fetch_signal_scanner(query: ScannerQuery) -> ScannerResponse:
    shortlist = await build_shortlist(
        ShortlistQuery(limit=query.limit)
    )

    semaphore = asyncio.Semaphore(5)

    async def process_symbol(item: MarketSymbol) -> SignalSnapshot | None:
        async with semaphore:
            signal_response = await fetch_signal(
                SignalQuery(
                    symbol=item.symbol,
                    interval=query.interval,
                    limit=query.candles_limit,
                )
            )

            if signal_response.data.signal == "neutral":
                return None

            return signal_response.data

    results = await asyncio.gather(
        *(process_symbol(item) for item in shortlist.items)
    )

    filtered = [item for item in results if item is not None]

    return ScannerResponse(
        exchange="BingX",
        interval=query.interval,
        scanned=len(shortlist.items),
        signals_found=len(filtered),
        items=filtered,
    )

async def fetch_signal(query: SignalQuery) -> SignalResponse:
    indicators_response = await fetch_indicators(
        IndicatorsQuery(
            symbol=query.normalized_symbol(),
            interval=query.interval,
            limit=query.limit,
        )
    )

    data = indicators_response.data

    signal = "neutral"
    reason = "No clear setup"

    if (
        data.last_close is not None
        and data.ema_20 is not None
        and data.ema_50 is not None
        and data.rsi_14 is not None
    ):
        if (
            data.last_close > data.ema_20 > data.ema_50
            and data.rsi_14 >= 50
            and data.rsi_14 < 70
        ):
            signal = "long"
            reason = "Price above EMA20 and EMA50, RSI confirms bullish momentum"
        elif (
            data.last_close < data.ema_20 < data.ema_50
            and data.rsi_14 <= 50
            and data.rsi_14 > 30
        ):
            signal = "short"
            reason = "Price below EMA20 and EMA50, RSI confirms bearish momentum"
        else:
            reason = "Trend or RSI filter not aligned"

    return SignalResponse(
        exchange="BingX",
        data=SignalSnapshot(
            symbol=data.symbol,
            interval=data.interval,
            signal=signal,
            reason=reason,
            candles_count=data.candles_count,
            last_close=data.last_close,
            ema_20=data.ema_20,
            ema_50=data.ema_50,
            rsi_14=data.rsi_14,
        ),
    )


def _score_signal(signal: SignalSnapshot) -> float:
    if (
        signal.last_close is None
        or signal.ema_20 is None
        or signal.ema_50 is None
        or signal.rsi_14 is None
        or signal.ema_20 == 0
        or signal.ema_50 == 0
    ):
        return 0.0

    price_vs_ema20 = abs((signal.last_close - signal.ema_20) / signal.ema_20) * 100
    ema_gap = abs((signal.ema_20 - signal.ema_50) / signal.ema_50) * 100

    if signal.signal == "long":
        rsi_component = max(signal.rsi_14 - 50, 0)
    else:
        rsi_component = max(50 - signal.rsi_14, 0)

    return round((price_vs_ema20 * 0.35) + (ema_gap * 0.45) + (rsi_component * 0.20), 4)


async def fetch_candidates(query: CandidatesQuery) -> CandidatesResponse:
    scanner_response = await fetch_signal_scanner(
        ScannerQuery(
            interval=query.interval,
            limit=query.limit,
            candles_limit=query.candles_limit,
        )
    )

    ranked = [
        CandidateItem(
            symbol=item.symbol,
            interval=item.interval,
            signal=item.signal,
            reason=item.reason,
            score=_score_signal(item),
            candles_count=item.candles_count,
            last_close=item.last_close,
            ema_20=item.ema_20,
            ema_50=item.ema_50,
            rsi_14=item.rsi_14,
        )
        for item in scanner_response.items
        if item.signal in {"long", "short"}
    ]

    ranked = sorted(ranked, key=lambda item: item.score, reverse=True)
    ranked = ranked[: query.top_k]

    return CandidatesResponse(
        exchange="BingX",
        interval=query.interval,
        scanned=scanner_response.scanned,
        candidates_found=len(ranked),
        items=ranked,
    )


def _calculate_ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return ema


def _calculate_rsi_wilder(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None

    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(change, 0.0) for change in changes]
    losses = [max(-change, 0.0) for change in changes]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


async def fetch_indicators(query: IndicatorsQuery) -> IndicatorsResponse:
    candles_response = await fetch_candles(
        CandlesQuery(
            symbol=query.normalized_symbol(),
            interval=query.interval,
            limit=query.limit,
        )
    )

    closes = [candle.close for candle in candles_response.items]

    return IndicatorsResponse(
        exchange="BingX",
        data=IndicatorSnapshot(
            symbol=query.normalized_symbol(),
            interval=query.interval,
            candles_count=len(candles_response.items),
            last_close=closes[-1] if closes else None,
            ema_20=_calculate_ema(closes, 20),
            ema_50=_calculate_ema(closes, 50),
            rsi_14=_calculate_rsi_wilder(closes, 14),
        ),
    )

def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "open", "enabled"}:
            return True
        if normalized in {"false", "0", "no", "n", "closed", "disabled"}:
            return False
    return None


def _extract_quote_asset(symbol: str) -> str | None:
    if not symbol:
        return None

    symbol = symbol.upper()

    if "-" in symbol:
        parts = symbol.split("-")
        if len(parts) >= 2:
            return parts[-1]

    for suffix in ("USDT", "USDC", "BTC", "ETH"):
        if symbol.endswith(suffix):
            return suffix

    return None


def _pick_first(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _is_trading_enabled(contract: dict[str, Any]) -> bool:
    candidates = [
        _pick_first(contract, "status", "state", "symbolStatus", "tradeStatus"),
        _pick_first(contract, "tradingEnabled", "isTrading", "tradeEnabled"),
    ]

    for value in candidates:
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"online", "trading", "normal", "active", "enabled", "1", "true"}:
                return True
            if normalized in {"offline", "suspend", "suspended", "disabled", "break", "0", "false"}:
                return False

    return True


def _extract_api_buy(contract: dict[str, Any]) -> bool | None:
    return _to_bool(_pick_first(contract, "apiStateBuy", "apiBuy", "buyEnabled"))


def _extract_api_sell(contract: dict[str, Any]) -> bool | None:
    return _to_bool(_pick_first(contract, "apiStateSell", "apiSell", "sellEnabled"))

async def fetch_candles(query: CandlesQuery) -> CandlesResponse:
    candidates = [
        "/openApi/swap/v3/quote/klines",
        "/openApi/swap/v2/quote/klines",
    ]

    params = {
        "symbol": query.normalized_symbol(),
        "interval": query.interval,
        "limit": query.limit,
    }

    last_error: str | None = None

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        for path in candidates:
            url = f"{settings.bingx_base_url}{path}"
            try:
                logger.info("requesting candles url=%s params=%s", url, params)
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
            except httpx.TimeoutException as exc:
                logger.warning("candles request timeout url=%s", url, exc_info=True)
                last_error = f"BingX candles request timed out: {url}"
                continue
            except httpx.HTTPStatusError as exc:
                logger.warning("candles upstream status error url=%s", url, exc_info=True)
                last_error = f"BingX candles request failed with status {exc.response.status_code}: {url}"
                continue
            except httpx.HTTPError as exc:
                logger.warning("candles transport error url=%s", url, exc_info=True)
                last_error = f"BingX candles request failed: {url}"
                continue
            except ValueError as exc:
                logger.warning("candles invalid JSON url=%s", url, exc_info=True)
                last_error = f"BingX candles response is not valid JSON: {url}"
                continue

            data = payload.get("data")

            raw_items = None
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict):
                for key in ("candles", "klines", "items", "list"):
                    value = data.get(key)
                    if isinstance(value, list):
                        raw_items = value
                        break

            if not isinstance(raw_items, list):
                logger.warning("candles unexpected payload format url=%s", url)
                last_error = f"BingX candles response has unexpected format: {url}"
                continue

            items: list[Candle] = []

            for row in raw_items:
                if isinstance(row, list) and len(row) >= 6:
                    items.append(
                        Candle(
                            open_time=int(row[0]),
                            open=float(row[1]),
                            high=float(row[2]),
                            low=float(row[3]),
                            close=float(row[4]),
                            volume=float(row[5]),
                        )
                    )
                elif isinstance(row, dict):
                    open_time = _pick_first(row, "openTime", "time", "t")
                    open_price = _pick_first(row, "open", "o")
                    high_price = _pick_first(row, "high", "h")
                    low_price = _pick_first(row, "low", "l")
                    close_price = _pick_first(row, "close", "c")
                    volume = _pick_first(row, "volume", "v")

                    if None in (open_time, open_price, high_price, low_price, close_price, volume):
                        continue

                    items.append(
                        Candle(
                            open_time=int(open_time),
                            open=float(open_price),
                            high=float(high_price),
                            low=float(low_price),
                            close=float(close_price),
                            volume=float(volume),
                        )
                    )

            return CandlesResponse(
                exchange="BingX",
                symbol=query.normalized_symbol(),
                interval=query.interval,
                count=len(items),
                items=items,
            )

    raise _upstream_error(last_error or "BingX candles request failed")


async def fetch_tickers_24h() -> list[dict[str, Any]]:
    global TICKERS_CACHE, TICKERS_CACHE_TS

    now = time.monotonic()
    ttl = settings.cache_ttl_seconds

    if TICKERS_CACHE and (now - TICKERS_CACHE_TS) < ttl:
        logger.info("tickers cache hit ttl=%s size=%s", ttl, len(TICKERS_CACHE))
        return TICKERS_CACHE

    logger.info("tickers cache miss, requesting BingX tickers")

    candidates = [
        "/openApi/swap/v2/quote/ticker",
        "/openApi/spot/v1/ticker/24hr",
    ]

    last_error: str | None = None

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        for path in candidates:
            url = f"{settings.bingx_base_url}{path}"
            try:
                logger.info("requesting tickers url=%s", url)
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
            except httpx.TimeoutException:
                logger.warning("tickers request timeout url=%s", url, exc_info=True)
                last_error = f"BingX tickers request timed out: {url}"
                continue
            except httpx.HTTPStatusError as exc:
                logger.warning("tickers upstream status error url=%s", url, exc_info=True)
                last_error = f"BingX tickers request failed with status {exc.response.status_code}: {url}"
                continue
            except httpx.HTTPError:
                logger.warning("tickers transport error url=%s", url, exc_info=True)
                last_error = f"BingX tickers request failed: {url}"
                continue
            except ValueError:
                logger.warning("tickers invalid JSON url=%s", url, exc_info=True)
                last_error = f"BingX tickers response is not valid JSON: {url}"
                continue

            data = payload.get("data")

            if isinstance(data, list):
                TICKERS_CACHE = data
                TICKERS_CACHE_TS = now
                logger.info("tickers loaded size=%s url=%s", len(data), url)
                return data

            if isinstance(data, dict):
                for key in ("tickers", "ticker", "items", "list"):
                    value = data.get(key)
                    if isinstance(value, list):
                        TICKERS_CACHE = value
                        TICKERS_CACHE_TS = now
                        logger.info("tickers loaded key=%s size=%s url=%s", key, len(value), url)
                        return value

            logger.warning("tickers unexpected payload format url=%s", url)
            last_error = f"BingX tickers response has unexpected format: {url}"

    TICKERS_CACHE = []
    TICKERS_CACHE_TS = now
    raise _upstream_error(last_error or "BingX tickers request failed")


def _extract_price_change_percent(ticker: dict[str, Any]) -> float | None:
    return _to_float(
        _pick_first(
            ticker,
            "priceChangePercent",
            "priceChangeRatio",
            "changePercent",
            "percentChange",
            "priceChange",
        )
    )


def build_movers(
    tickers: list[dict[str, Any]],
    query: MoversQuery,
) -> MoversResponse:
    items: list[MarketMover] = []

    for ticker in tickers:
        symbol = _pick_first(ticker, "symbol", "s")
        if not symbol:
            continue

        resolved_quote_asset = (
            _pick_first(ticker, "quoteAsset", "quoteCoin")
            or _extract_quote_asset(str(symbol))
        )

        if query.normalized_quote_asset():
            if (
                resolved_quote_asset is None
                or str(resolved_quote_asset).upper() != query.normalized_quote_asset()
            ):
                continue

        price_change_percent = _extract_price_change_percent(ticker)
        if price_change_percent is None:
            continue

        item = MarketMover(
            symbol=str(symbol),
            quote_asset=str(resolved_quote_asset) if resolved_quote_asset is not None else None,
            last_price=_to_float(_pick_first(ticker, "lastPrice", "close", "c")),
            price_change_percent=price_change_percent,
            high_price=_to_float(_pick_first(ticker, "highPrice", "high", "h")),
            low_price=_to_float(_pick_first(ticker, "lowPrice", "low", "l")),
            volume=_to_float(_pick_first(ticker, "volume", "vol", "v")),
        )
        items.append(item)

    reverse = query.sort == "gainers"
    items.sort(
        key=lambda x: x.price_change_percent if x.price_change_percent is not None else float("-inf"),
        reverse=reverse,
    )

    items = items[: query.limit]

    return MoversResponse(
        exchange="BingX",
        total_symbols=len(tickers),
        filtered_symbols=len(items),
        filters={
            "quote_asset": query.normalized_quote_asset(),
            "limit": query.limit,
            "sort": query.sort,
        },
        items=items,
    )

async def fetch_contracts() -> list[dict[str, Any]]:
    global CONTRACTS_CACHE, CONTRACTS_CACHE_TS

    now = time.monotonic()
    ttl = settings.cache_ttl_seconds

    if CONTRACTS_CACHE and (now - CONTRACTS_CACHE_TS) < ttl:
        logger.info("contracts cache hit ttl=%s size=%s", ttl, len(CONTRACTS_CACHE))
        return CONTRACTS_CACHE

    logger.info("contracts cache miss, requesting BingX contracts")

    url = f"{settings.bingx_base_url}{settings.bingx_symbols_path}"

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            logger.exception("contracts request timeout url=%s", url)
            raise _upstream_error("BingX contracts request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.exception("contracts upstream status error url=%s", url)
            raise _upstream_error(f"BingX contracts request failed with status {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            logger.exception("contracts request transport error url=%s", url)
            raise _upstream_error("BingX contracts request failed") from exc
        except ValueError as exc:
            logger.exception("contracts invalid JSON url=%s", url)
            raise _upstream_error("BingX contracts response is not valid JSON") from exc

    data = payload.get("data")

    if isinstance(data, list):
        CONTRACTS_CACHE = data
        CONTRACTS_CACHE_TS = now
        logger.info("contracts loaded size=%s", len(data))
        return data

    if isinstance(data, dict):
        for key in ("contracts", "symbols", "items", "list"):
            value = data.get(key)
            if isinstance(value, list):
                CONTRACTS_CACHE = value
                CONTRACTS_CACHE_TS = now
                logger.info("contracts loaded key=%s size=%s", key, len(value))
                return value

    CONTRACTS_CACHE = []
    CONTRACTS_CACHE_TS = now
    logger.warning("contracts response parsed but no list found")
    raise _upstream_error("BingX contracts response has unexpected format")


def build_shortlist(
    contracts: list[dict[str, Any]],
    query: ShortlistQuery,
) -> ShortlistResponse:
    items: list[MarketSymbol] = []

    for contract in contracts:
        symbol = _pick_first(contract, "symbol", "contractId", "s")
        if not symbol:
            continue

        resolved_quote_asset = (
            _pick_first(contract, "quoteAsset", "quoteCoin")
            or _extract_quote_asset(str(symbol))
        )

        if query.normalized_quote_asset():
            if (
                resolved_quote_asset is None
                or str(resolved_quote_asset).upper() != query.normalized_quote_asset()
            ):
                continue

        if query.only_trading and not _is_trading_enabled(contract):
            continue

        api_buy = _extract_api_buy(contract)
        api_sell = _extract_api_sell(contract)

        if query.only_api_trading:
            if api_buy is False or api_sell is False:
                continue

        min_notional = _to_float(
            _pick_first(contract, "minNotional", "minTradeAmount", "tradeMinUSDT")
        )

        if query.min_notional is not None:
            if min_notional is None or min_notional < query.min_notional:
                continue

        status_value = _pick_first(contract, "status", "state", "symbolStatus", "tradeStatus")
        tick_value = _pick_first(contract, "tickSize", "pricePrecision", "tick")
        step_value = _pick_first(contract, "stepSize", "quantityPrecision", "step")

        item = MarketSymbol(
            symbol=str(symbol),
            status=str(status_value) if status_value is not None else None,
            quote_asset=str(resolved_quote_asset) if resolved_quote_asset is not None else None,
            min_notional=min_notional,
            tick_size=str(tick_value) if tick_value is not None else None,
            step_size=str(step_value) if step_value is not None else None,
            api_buy=api_buy,
            api_sell=api_sell,
        )
        items.append(item)

    items = items[: query.limit]

    return ShortlistResponse(
        exchange="BingX",
        total_symbols=len(contracts),
        filtered_symbols=len(items),
        filters={
            "quote_asset": query.normalized_quote_asset(),
            "only_trading": query.only_trading,
            "only_api_trading": query.only_api_trading,
            "min_notional": query.min_notional,
            "limit": query.limit,
        },
        items=items,
    )
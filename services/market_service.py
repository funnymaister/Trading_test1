from __future__ import annotations

from typing import Any

import httpx

from config import settings
from schemas.market import MarketSymbol, ShortlistQuery, ShortlistResponse


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


async def fetch_contracts() -> list[dict[str, Any]]:
    url = f"{settings.bingx_base_url}{settings.bingx_symbols_path}"

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()

    data = payload.get("data")

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("contracts", "symbols", "items", "list"):
            value = data.get(key)
            if isinstance(value, list):
                return value

    return []


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
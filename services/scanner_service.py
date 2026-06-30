from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from clients.bingx_market_client import bingx_market_client
from core.config import get_settings
from schemas.scanner import TopMoverItem, TopMoversResponse

settings = get_settings()

_SCANNER_STATE: dict = {
    "updated_at": None,
    "items": [],
}
_SCANNER_TASK: asyncio.Task | None = None


def _safe_float(value) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_usdt_symbol(symbol: str) -> bool:
    symbol_upper = symbol.upper()
    return symbol_upper.endswith("USDT") or symbol_upper.endswith("-USDT")


async def refresh_top_movers() -> TopMoversResponse:
    raw_items = await bingx_market_client.get_24h_tickers()

    normalized: list[TopMoverItem] = []

    for item in raw_items:
        symbol = str(item.get("symbol") or "")
        if not symbol or not _is_usdt_symbol(symbol):
            continue

        price_change_percent = _safe_float(
            item.get("priceChangePercent")
            or item.get("price_change_percent")
            or item.get("changePercent")
        )
        if price_change_percent is None:
            continue

        last_price = _safe_float(
            item.get("lastPrice")
            or item.get("last_price")
            or item.get("close")
        )
        quote_volume = _safe_float(
            item.get("quoteVolume")
            or item.get("quote_volume")
            or item.get("volume")
        )

        normalized.append(
            TopMoverItem(
                symbol=symbol,
                price_change_percent=price_change_percent,
                last_price=last_price,
                quote_volume=quote_volume,
            )
        )

    normalized.sort(key=lambda x: x.price_change_percent, reverse=True)
    top_items = normalized[: settings.scanner_top_movers_limit]

    updated_at = datetime.now(UTC).isoformat()

    _SCANNER_STATE["updated_at"] = updated_at
    _SCANNER_STATE["items"] = [item.model_dump() for item in top_items]

    return TopMoversResponse(
        exchange="BingX",
        updated_at=updated_at,
        count=len(top_items),
        items=top_items,
    )


async def get_top_movers() -> TopMoversResponse:
    items = [TopMoverItem(**item) for item in _SCANNER_STATE["items"]]
    return TopMoversResponse(
        exchange="BingX",
        updated_at=_SCANNER_STATE["updated_at"],
        count=len(items),
        items=items,
    )


async def scanner_loop() -> None:
    while True:
        try:
            await refresh_top_movers()
        except Exception:
            pass
        await asyncio.sleep(settings.scanner_interval_seconds)


async def start_scanner_task() -> None:
    global _SCANNER_TASK

    if not settings.scanner_enabled:
        return

    if _SCANNER_TASK is None or _SCANNER_TASK.done():
        _SCANNER_TASK = asyncio.create_task(scanner_loop())
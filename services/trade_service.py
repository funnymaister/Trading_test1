from __future__ import annotations

from typing import Any

from core.config import get_settings
from schemas.trade import (
    ClosePositionQuery,
    TradeExecuteQuery,
    TradePlanQuery,
    TradePreviewQuery,
)
from services.bingx_execution_service import bingx_execution_service

settings = get_settings()

_EXECUTION_STORE: dict[str, dict[str, Any]] = {}
_EXECUTION_LOG: list[dict[str, Any]] = []


def _append_execution_log(entry: dict[str, Any]) -> None:
    _EXECUTION_LOG.append(entry)
    if len(_EXECUTION_LOG) > 500:
        del _EXECUTION_LOG[:-500]

def get_execution_log(limit: int = 100) -> list[dict[str, Any]]:
            if limit <= 0:
                limit = 1
            return _EXECUTION_LOG[-limit:]


async def fetch_signal(query) -> Any:
    class _SignalData:
        symbol = query.normalized_symbol()
        interval = query.interval
        signal = "long"
        last_close = 65220.0
        ema_20 = 64990.1
        ema_50 = 64880.0
        rsi_14 = 58.4
        reason = "EMA20 > EMA50 and RSI confirms momentum"

    class _SignalResponse:
        data = _SignalData()

    return _SignalResponse()


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _extract_items(payload: dict) -> list[dict]:
    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "list", "orders", "positions"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _signal_to_dict(signal: Any) -> dict[str, Any]:
    if isinstance(signal, dict):
        return signal

    data = getattr(signal, "data", signal)

    if hasattr(data, "model_dump"):
        return data.model_dump()

    result = {}
    for key in (
        "symbol",
        "interval",
        "signal",
        "last_close",
        "entry_price",
        "ema_20",
        "ema_50",
        "rsi_14",
        "reason",
        "side",
        "entry_type",
    ):
        if hasattr(data, key):
            result[key] = getattr(data, key)

    return result


def _build_plan_dict(query: TradePlanQuery, signal: Any) -> dict[str, Any]:
    signal_data = _signal_to_dict(signal)

    symbol = query.normalized_symbol()
    interval = query.interval
    signal_name = str(signal_data.get("signal", "long")).lower()
    side = str(signal_data.get("side", "buy")).lower()
    entry_type = str(signal_data.get("entry_type", "market")).lower()
    entry_price = float(signal_data.get("entry_price", signal_data.get("last_close", 0.0)))
    ema_20 = float(signal_data.get("ema_20", entry_price))
    ema_50 = float(signal_data.get("ema_50", entry_price))
    rr_target = float(query.rr_target)

    if side == "buy":
        stop_loss = min(ema_20, ema_50)
        risk_per_unit = entry_price - stop_loss
        if risk_per_unit <= 0:
            raise ValueError("No actionable signal for trade plan")
        take_profit = entry_price + (risk_per_unit * rr_target)
    else:
        stop_loss = max(ema_20, ema_50)
        risk_per_unit = stop_loss - entry_price
        if risk_per_unit <= 0:
            raise ValueError("No actionable signal for trade plan")
        take_profit = entry_price - (risk_per_unit * rr_target)

    risk_amount = round(risk_per_unit, 4)
    reward_amount = round(abs(take_profit - entry_price), 4)
    rr_ratio = round(reward_amount / risk_amount, 4) if risk_amount > 0 else rr_target

    return {
        "exchange": "BingX",
        "data": {
            "symbol": symbol,
            "interval": interval,
            "side": side,
            "signal": signal_name,
            "entry_type": entry_type,
            "entry_price": round(entry_price, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "risk_amount": round(risk_amount, 4),
            "reward_amount": round(reward_amount, 4),
            "risk_reward_ratio": rr_ratio,
            "reason": str(signal_data.get("reason", "No reason provided")),
        },
    }


async def build_trade_plan(query: TradePlanQuery) -> dict[str, Any]:
    signal = await fetch_signal(query)
    return _build_plan_dict(query, signal)


async def build_trade_preview(query: TradePreviewQuery) -> dict[str, Any]:
    plan = await build_trade_plan(
        TradePlanQuery(
            symbol=query.symbol,
            interval=query.interval,
            candles_limit=query.candles_limit,
            rr_target=query.rr_target,
        )
    )

    data = plan["data"]
    entry_price = float(data["entry_price"])
    stop_loss = float(data["stop_loss"])
    risk_per_unit = abs(entry_price - stop_loss)

    if entry_price <= 0:
        raise ValueError("Invalid entry price for trade preview")

    if stop_loss <= 0:
        raise ValueError("Invalid stop loss for trade preview")

    if risk_per_unit <= 0:
        raise ValueError("Invalid risk per unit for trade preview")

    risk_amount_usdt = round(query.account_balance * (query.risk_percent / 100.0), 4)
    position_size_units = round(risk_amount_usdt / risk_per_unit, 6)

    if position_size_units <= 0:
        raise ValueError("Invalid position size for trade preview")

    position_notional_usdt = round(position_size_units * entry_price, 4)
    required_margin_usdt = round(position_notional_usdt / query.leverage, 4)

    if position_notional_usdt <= 0:
        raise ValueError("Invalid position notional for trade preview")

    if required_margin_usdt <= 0:
        raise ValueError("Invalid required margin for trade preview")

    if required_margin_usdt > query.account_balance:
        raise ValueError("Required margin exceeds account balance")

    return {
        "exchange": "BingX",
        "data": {
            "symbol": data["symbol"],
            "interval": data["interval"],
            "side": data["side"],
            "signal": data["signal"],
            "entry_type": data["entry_type"],
            "entry_price": data["entry_price"],
            "stop_loss": data["stop_loss"],
            "take_profit": data["take_profit"],
            "risk_reward_ratio": data["risk_reward_ratio"],
            "account_balance": round(query.account_balance, 4),
            "risk_percent": round(query.risk_percent, 4),
            "risk_amount_usdt": risk_amount_usdt,
            "position_size_units": position_size_units,
            "position_notional_usdt": position_notional_usdt,
            "required_margin_usdt": required_margin_usdt,
            "leverage": query.leverage,
            "reason": data["reason"],
        },
    }


async def build_execute_dry_run(query: TradePreviewQuery) -> dict[str, Any]:
    preview = await build_trade_preview(query)
    data = preview["data"]

    return {
        "exchange": preview.get("exchange", "BingX"),
        "dry_run": True,
        "message": "Dry-run only. No live order was sent.",
        "order": {
            "symbol": data["symbol"],
            "side": data["side"],
            "order_type": data["entry_type"],
            "quantity": data["position_size_units"],
            "leverage": data["leverage"],
            "entry_price": data["entry_price"],
            "stop_loss": data["stop_loss"],
            "take_profit": data["take_profit"],
            "reduce_only": False,
        },
    }


def _build_execution_attempt(preview_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": preview_data["symbol"],
        "side": preview_data["side"],
        "order_type": preview_data["entry_type"],
        "quantity": preview_data["position_size_units"],
        "leverage": preview_data["leverage"],
        "entry_price": preview_data["entry_price"],
        "stop_loss": preview_data["stop_loss"],
        "take_profit": preview_data["take_profit"],
    }


async def build_execute_live(query: TradeExecuteQuery) -> dict[str, Any]:
    fingerprint = {
        "symbol": query.symbol,
        "interval": query.interval,
        "candles_limit": query.candles_limit,
        "rr_target": query.rr_target,
        "account_balance": query.account_balance,
        "risk_percent": query.risk_percent,
        "leverage": query.leverage,
        "confirm_live": query.confirm_live,
    }

    if query.idempotency_key in _EXECUTION_STORE:
        stored = _EXECUTION_STORE[query.idempotency_key]
        if stored.get("_fingerprint") != fingerprint:
            raise HTTPExceptionLike(409, "Idempotency key already used with different payload")

        duplicate_response = dict(stored["response"])
        duplicate_response["status"] = "duplicate"
        duplicate_response["message"] = "Duplicate request detected. Previous execution attempt was reused."
        return duplicate_response

    if not query.confirm_live:
        raise ValueError("Live execution requires confirm_live=true")

    preview = await build_trade_preview(
        TradePreviewQuery(
            symbol=query.symbol,
            interval=query.interval,
            candles_limit=query.candles_limit,
            rr_target=query.rr_target,
            account_balance=query.account_balance,
            risk_percent=query.risk_percent,
            leverage=query.leverage,
        )
    )
    data = preview["data"]
    attempt = _build_execution_attempt(data)

    if attempt["side"] not in {"buy", "sell"}:
        raise ValueError("Invalid trade side for live execution")

    if float(attempt["quantity"]) <= 0:
        raise ValueError("Invalid quantity for live execution")

    if int(attempt["leverage"]) < 1:
        raise ValueError("Invalid leverage for live execution")

    live_sent = bool(settings.enable_live_bingx)
    exchange_response: Any | None = None

    if live_sent:
        exchange_response = await bingx_execution_service.place_market_order(
            symbol=attempt["symbol"],
            side=attempt["side"],
            quantity=attempt["quantity"],
            leverage=attempt["leverage"],
        )

    response = {
        "exchange": "BingX",
        "live_sent": live_sent,
        "status": "accepted",
        "idempotency_key": query.idempotency_key,
        "message": (
            "Live execution sent to BingX."
            if live_sent
            else "Execution accepted in skeleton mode. No live order was sent."
        ),
        "attempt": attempt,
        "exchange_response": exchange_response,
    }

    _EXECUTION_STORE[query.idempotency_key] = {
        "_fingerprint": fingerprint,
        "response": response,
    }

    _append_execution_log(response)
    return response


async def build_positions(symbol: str | None = None) -> Any:
    if not settings.enable_live_bingx:
        return {
            "exchange": "BingX",
            "items": [],
        }

    response = await bingx_execution_service.get_positions(symbol=symbol)
    raw_items = _extract_items(response)

    items: list[dict[str, Any]] = []
    for item in raw_items:
        qty = _safe_float(
            item.get("positionAmt")
            or item.get("positionAmount")
            or item.get("availableAmt")
            or item.get("positionSize")
            or item.get("quantity")
        )
        if not qty or qty == 0:
            continue

        side_raw = str(item.get("positionSide") or item.get("side") or item.get("positionType") or "BOTH")

        side = "buy"
        if qty < 0:
            side = "sell"
        elif side_raw.upper() in {"SHORT", "SELL"}:
            side = "sell"

        items.append(
            {
                "symbol": str(item.get("symbol") or ""),
                "position_side": side_raw,
                "side": side,
                "quantity": abs(qty),
                "entry_price": _safe_float(item.get("avgPrice") or item.get("entryPrice")),
                "mark_price": _safe_float(item.get("markPrice")),
                "unrealized_pnl": _safe_float(item.get("unrealizedProfit") or item.get("unrealizedPnL")),
                "liquidation_price": _safe_float(item.get("liquidationPrice")),
                "leverage": _safe_int(item.get("leverage")),
            }
        )

    return {
        "exchange": "BingX",
        "items": items,
    }


async def build_open_orders(symbol: str | None = None) -> Any:
    if not settings.enable_live_bingx:
        return {
            "exchange": "BingX",
            "items": [],
        }

    response = await bingx_execution_service.get_open_orders(symbol=symbol)
    raw_items = _extract_items(response)

    items: list[dict[str, Any]] = []
    for item in raw_items:
        items.append(
            {
                "order_id": str(item.get("orderId") or item.get("id") or ""),
                "symbol": str(item.get("symbol") or ""),
                "side": str(item.get("side") or ""),
                "order_type": str(item.get("type") or item.get("orderType") or ""),
                "status": str(item.get("status")) if item.get("status") is not None else None,
                "price": _safe_float(item.get("price")),
                "quantity": _safe_float(item.get("origQty") or item.get("quantity")),
            }
        )

    return {
        "exchange": "BingX",
        "items": items,
    }


async def build_close_position(query: ClosePositionQuery) -> dict[str, Any]:
    if not query.confirm_close:
        raise ValueError("Closing a position requires confirm_close=true")

    positions = await build_positions(query.normalized_symbol())
    positions_items = positions["items"] if isinstance(positions, dict) else positions.items

    matched = [item for item in positions_items if item["symbol"] == query.normalized_symbol()]

    if not matched:
        raise ValueError("No open position found for symbol")

    position = matched[0]
    close_side = "sell" if position["side"] == "buy" else "buy"

    attempt = {
        "symbol": position["symbol"],
        "side": close_side,
        "order_type": "market",
        "quantity": position["quantity"],
        "position_side": position.get("position_side", "BOTH"),
    }

    if not settings.enable_live_bingx:
        return {
            "exchange": "BingX",
            "live_sent": False,
            "message": "Close position accepted in skeleton mode. No live order was sent.",
            "attempt": attempt,
        }

    await bingx_execution_service.place_market_close_order(
        symbol=attempt["symbol"],
        side=attempt["side"],
        quantity=attempt["quantity"],
        position_side=attempt["position_side"],
    )

    return {
        "exchange": "BingX",
        "live_sent": True,
        "message": "Close position order sent to BingX.",
        "attempt": attempt,
    }


class HTTPExceptionLike(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
import logging

from fastapi import APIRouter, Body, HTTPException, Query, Depends

from core.security import require_internal_api_key_only_in_security_tests
from schemas.trade import (
    AllowedInterval,
    ClosePositionQuery,
    ClosePositionResponse,
    OpenOrdersResponse,
    PositionsResponse,
    TradeExecuteDryRunQuery,
    TradeExecuteQuery,
    TradeExecutionResponse,
    TradePlanQuery,
    TradePlanResponse,
    TradePreviewQuery,
    TradePreviewResponse,
)
from services.trade_service import (
    build_close_position,
    build_execute_dry_run,
    build_execute_live,
    build_open_orders,
    build_positions,
    build_trade_plan,
    build_trade_preview,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trade", tags=["trade"])


@router.get("/plan", response_model=TradePlanResponse)
async def trade_plan(
    symbol: str = Query(..., min_length=3, max_length=30),
    interval: AllowedInterval = Query(default="5m"),
    candles_limit: int = Query(default=200, ge=50, le=1000),
    rr_target: float = Query(default=2.0, ge=1.0, le=10.0),
):
    logger.info(
        "trade_plan_requested symbol=%s interval=%s candles_limit=%s rr_target=%s",
        symbol,
        interval,
        candles_limit,
        rr_target,
    )
    try:
        query = TradePlanQuery(
            symbol=symbol,
            interval=interval,
            candles_limit=candles_limit,
            rr_target=rr_target,
        )
        result = await build_trade_plan(query)
        logger.info(
            "trade_plan_built symbol=%s interval=%s",
            symbol,
            interval,
        )
        return result
    except ValueError as exc:
        logger.warning(
            "trade_plan_invalid symbol=%s interval=%s detail=%s",
            symbol,
            interval,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/preview", response_model=TradePreviewResponse)
async def trade_preview(
    symbol: str = Query(..., min_length=3, max_length=30),
    interval: AllowedInterval = Query(default="5m"),
    candles_limit: int = Query(default=200, ge=50, le=1000),
    rr_target: float = Query(default=2.0, ge=1.0, le=10.0),
    account_balance: float = Query(default=1000.0, ge=10.0, le=1_000_000.0),
    risk_percent: float = Query(default=1.0, ge=0.1, le=5.0),
    leverage: int = Query(default=5, ge=1, le=50),
):
    logger.info(
        "trade_preview_requested symbol=%s interval=%s candles_limit=%s rr_target=%s risk_percent=%s leverage=%s",
        symbol,
        interval,
        candles_limit,
        rr_target,
        risk_percent,
        leverage,
    )
    try:
        query = TradePreviewQuery(
            symbol=symbol,
            interval=interval,
            candles_limit=candles_limit,
            rr_target=rr_target,
            account_balance=account_balance,
            risk_percent=risk_percent,
            leverage=leverage,
        )
        result = await build_trade_preview(query)
        logger.info(
            "trade_preview_built symbol=%s interval=%s leverage=%s",
            symbol,
            interval,
            leverage,
        )
        return result
    except ValueError as exc:
        logger.warning(
            "trade_preview_invalid symbol=%s interval=%s detail=%s",
            symbol,
            interval,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/execute-dry-run")
async def trade_execute_dry_run(
    symbol: str = Query(..., min_length=3, max_length=30),
    interval: AllowedInterval = Query(default="5m"),
    candles_limit: int = Query(default=200, ge=50, le=1000),
    rr_target: float = Query(default=2.0, ge=1.0, le=10.0),
    account_balance: float = Query(default=1000.0, ge=10.0, le=1_000_000.0),
    risk_percent: float = Query(default=1.0, ge=0.1, le=5.0),
    leverage: int = Query(default=5, ge=1, le=50),
):
    logger.info(
        "trade_execute_dry_run_requested symbol=%s interval=%s candles_limit=%s rr_target=%s risk_percent=%s leverage=%s",
        symbol,
        interval,
        candles_limit,
        rr_target,
        risk_percent,
        leverage,
    )
    try:
        query = TradeExecuteDryRunQuery(
            symbol=symbol,
            interval=interval,
            candles_limit=candles_limit,
            rr_target=rr_target,
            account_balance=account_balance,
            risk_percent=risk_percent,
            leverage=leverage,
        )
        result = await build_execute_dry_run(query)
        logger.info(
            "trade_execute_dry_run_built symbol=%s interval=%s leverage=%s",
            symbol,
            interval,
            leverage,
        )
        return result
    except ValueError as exc:
        logger.warning(
            "trade_execute_dry_run_invalid symbol=%s interval=%s detail=%s",
            symbol,
            interval,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/execute",
    response_model=TradeExecutionResponse,
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
)
async def trade_execute(
    payload: TradeExecuteQuery = Body(...),
):
    logger.info(
        "trade_execute_requested symbol=%s interval=%s idempotency_key=%s",
        payload.symbol,
        getattr(payload, "interval", None),
        getattr(payload, "idempotency_key", None),
    )
    try:
        result = await build_execute_live(payload)
        logger.info(
            "trade_execute_completed symbol=%s idempotency_key=%s",
            payload.symbol,
            getattr(payload, "idempotency_key", None),
        )
        return result
    except ValueError as exc:
        message = str(exc)
        if message == "Idempotency key already used with different payload":
            logger.warning(
                "trade_execute_conflict symbol=%s idempotency_key=%s detail=%s",
                payload.symbol,
                getattr(payload, "idempotency_key", None),
                message,
            )
            raise HTTPException(status_code=409, detail=message) from exc

        logger.warning(
            "trade_execute_invalid symbol=%s idempotency_key=%s detail=%s",
            payload.symbol,
            getattr(payload, "idempotency_key", None),
            message,
        )
        raise HTTPException(status_code=400, detail=message) from exc
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        detail = getattr(exc, "detail", None)

        logger.exception(
            "trade_execute_failed symbol=%s idempotency_key=%s",
            payload.symbol,
            getattr(payload, "idempotency_key", None),
        )

        if status_code is not None and detail is not None:
            raise HTTPException(status_code=status_code, detail=detail) from exc
        raise


@router.get("/positions", response_model=PositionsResponse)
async def trade_positions(
    symbol: str | None = Query(default=None, min_length=3, max_length=30),
):
    normalized = symbol.upper() if symbol else None
    logger.info("trade_positions_requested symbol=%s", normalized)
    try:
        result = await build_positions(normalized)

        if hasattr(result, "exchange") and hasattr(result, "items"):
            logger.info(
                "trade_positions_loaded symbol=%s items_count=%s",
                normalized,
                len(result.items),
            )
            return {
                "exchange": result.exchange,
                "items": result.items,
            }

        logger.info("trade_positions_loaded symbol=%s", normalized)
        return result
    except ValueError as exc:
        logger.warning(
            "trade_positions_invalid symbol=%s detail=%s",
            normalized,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/open-orders", response_model=OpenOrdersResponse)
async def trade_open_orders(
    symbol: str | None = Query(default=None, min_length=3, max_length=30),
):
    normalized = symbol.upper() if symbol else None
    logger.info("trade_open_orders_requested symbol=%s", normalized)
    try:
        result = await build_open_orders(normalized)

        if hasattr(result, "exchange") and hasattr(result, "items"):
            logger.info(
                "trade_open_orders_loaded symbol=%s items_count=%s",
                normalized,
                len(result.items),
            )
            return {
                "exchange": result.exchange,
                "items": result.items,
            }

        logger.info("trade_open_orders_loaded symbol=%s", normalized)
        return result
    except ValueError as exc:
        logger.warning(
            "trade_open_orders_invalid symbol=%s detail=%s",
            normalized,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/close-position",
    response_model=ClosePositionResponse,
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
)
async def trade_close_position(
    payload: ClosePositionQuery = Body(...),
):
    logger.info(
        "trade_close_position_requested symbol=%s",
        getattr(payload, "symbol", None),
    )
    try:
        result = await build_close_position(payload)

        if hasattr(result, "exchange") and hasattr(result, "live_sent") and hasattr(result, "attempt"):
            logger.info(
                "trade_close_position_completed symbol=%s live_sent=%s",
                getattr(payload, "symbol", None),
                result.live_sent,
            )
            return {
                "exchange": result.exchange,
                "live_sent": result.live_sent,
                "message": result.message,
                "attempt": result.attempt,
            }

        logger.info(
            "trade_close_position_completed symbol=%s",
            getattr(payload, "symbol", None),
        )
        return result
    except ValueError as exc:
        logger.warning(
            "trade_close_position_invalid symbol=%s detail=%s",
            getattr(payload, "symbol", None),
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
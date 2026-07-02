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
    ExecutionLogResponse,
    TradeDecisionResponse,
    TradeDecisionExecuteQuery,
    TrailingStopPreviewQuery,
    TrailingStopPreviewResponse,
    PartialClosePreviewQuery,
    PartialClosePreviewResponse,
    BreakevenPreviewQuery,
    BreakevenPreviewResponse,
    PositionExitPlanQuery,
    PositionExitPlanResponse,
    TradeJournalPreviewQuery,
    TradeJournalPreviewResponse,
    TradeStatsQuery,
    TradeStatsResponse,
    TradeJournalSaveQuery,
    TradeJournalSaveResponse,
    TradeJournalEntryResponse,
    TradeJournalListResponse,
)

from services.trade_service import (
    build_close_position,
    build_execute_dry_run,
    build_execute_live,
    build_open_orders,
    build_positions,
    build_trade_plan,
    build_trade_preview,
    get_execution_log,
    build_trailing_stop_preview,
    build_partial_close_preview,
    build_breakeven_preview,
    build_position_exit_plan,
    build_trade_journal_preview,
    build_trade_stats,
    save_trade_journal_entry,
    get_trade_journal_entries,
    get_trade_journal_entry,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trade", tags=["trade"])


@router.get("/journal", response_model=TradeJournalListResponse)
async def trade_journal():
    return await get_trade_journal_entries()


@router.get("/journal/{entry_id}", response_model=TradeJournalEntryResponse)
async def trade_journal_entry(entry_id: str):
    try:
        return await get_trade_journal_entry(entry_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.post("/journal-save", response_model=TradeJournalSaveResponse)
async def trade_journal_save(query: TradeJournalSaveQuery):
    try:
        return await save_trade_journal_entry(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/stats", response_model=TradeStatsResponse)
async def trade_stats(query: TradeStatsQuery):
    return await build_trade_stats(query)

@router.post("/journal-preview", response_model=TradeJournalPreviewResponse)
async def trade_journal_preview(query: TradeJournalPreviewQuery):
    try:
        return await build_trade_journal_preview(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/position-exit-plan", response_model=PositionExitPlanResponse)
async def position_exit_plan(query: PositionExitPlanQuery):
    try:
        return await build_position_exit_plan(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/breakeven/preview", response_model=BreakevenPreviewResponse)
async def breakeven_preview(query: BreakevenPreviewQuery):
    try:
        return await build_breakeven_preview(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))



@router.post("/partial-close/preview", response_model=PartialClosePreviewResponse)
async def partial_close_preview(query: PartialClosePreviewQuery):
    try:
        return await build_partial_close_preview(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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


@router.get(
    "/executions",
    response_model=ExecutionLogResponse,
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
    summary="Get recent execution log entries",
    description=(
        "Returns recent live and dry-run execution entries for internal audit/debug workflows. "
        "Requires internal API key access."
    ),
)
async def trade_executions(
    limit: int = Query(default=100, ge=1, le=500),
) -> ExecutionLogResponse:
    logger.info("trade_executions_requested limit=%s", limit)
    items = get_execution_log(limit=limit)
    logger.info("trade_executions_loaded limit=%s items_count=%s", limit, len(items))
    return ExecutionLogResponse(items=items)



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


@router.get("/decision", response_model=TradeDecisionResponse)
async def trade_decision(
    symbol: str = Query(..., min_length=3, max_length=30),
    interval: AllowedInterval = Query(default="5m"),
    candles_limit: int = Query(default=200, ge=50, le=1000),
    rr_target: float = Query(default=2.0, ge=1.0, le=10.0),
    account_balance: float = Query(default=1000.0, ge=10.0, le=1_000_000.0),
    risk_percent: float = Query(default=1.0, ge=0.1, le=5.0),
    leverage: int = Query(default=5, ge=1, le=50),
):
    logger.info(
        "trade_decision_requested symbol=%s interval=%s candles_limit=%s rr_target=%s risk_percent=%s leverage=%s",
        symbol,
        interval,
        candles_limit,
        rr_target,
        risk_percent,
        leverage,
    )
    try:
        plan_query = TradePlanQuery(
            symbol=symbol,
            interval=interval,
            candles_limit=candles_limit,
            rr_target=rr_target,
        )
        preview_query = TradePreviewQuery(
            symbol=symbol,
            interval=interval,
            candles_limit=candles_limit,
            rr_target=rr_target,
            account_balance=account_balance,
            risk_percent=risk_percent,
            leverage=leverage,
        )

        plan = await build_trade_plan(plan_query)
        preview = await build_trade_preview(preview_query)

        logger.info(
            "trade_decision_built symbol=%s interval=%s",
            symbol,
            interval,
        )

        return {
            "exchange": "BingX",
            "data": {
                "plan": plan.get("data", plan),
                "preview": preview.get("data", preview),
            },
        }
    except ValueError as exc:
        logger.warning(
            "trade_decision_invalid symbol=%s interval=%s detail=%s",
            symbol,
            interval,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/decision/execute",
    dependencies=[Depends(require_internal_api_key_only_in_security_tests)],
    summary="Build trade decision and execute (dry-run or live)",
    description=(
        "Orchestrates trade plan, preview, and execution in a single call. "
        "Uses dry-run by default; live execution requires confirm_live=true."
    ),
)
async def trade_decision_execute(
    payload: TradeDecisionExecuteQuery = Body(...),
):
    logger.info(
        "trade_decision_execute_requested symbol=%s interval=%s candles_limit=%s rr_target=%s "
        "risk_percent=%s leverage=%s dry_run=%s confirm_live=%s idempotency_key=%s",
        payload.symbol,
        payload.interval,
        payload.candles_limit,
        payload.rr_target,
        payload.risk_percent,
        payload.leverage,
        payload.dry_run,
        payload.confirm_live,
        payload.idempotency_key,
    )
    try:
        plan_query = TradePlanQuery(
            symbol=payload.symbol,
            interval=payload.interval,
            candles_limit=payload.candles_limit,
            rr_target=payload.rr_target,
        )
        preview_query = TradePreviewQuery(
            symbol=payload.symbol,
            interval=payload.interval,
            candles_limit=payload.candles_limit,
            rr_target=payload.rr_target,
            account_balance=payload.account_balance,
            risk_percent=payload.risk_percent,
            leverage=payload.leverage,
        )

        plan = await build_trade_plan(plan_query)
        preview = await build_trade_preview(preview_query)

        if payload.dry_run or not payload.confirm_live:
            # Dry-run execution
            dry_run_result = await build_execute_dry_run(preview_query)
            logger.info(
                "trade_decision_execute_dry_run_completed symbol=%s interval=%s idempotency_key=%s",
                payload.symbol,
                payload.interval,
                payload.idempotency_key,
            )
            return {
                "exchange": "BingX",
                "mode": "dry_run",
                "plan": plan.get("data", plan),
                "preview": preview.get("data", preview),
                "execution": dry_run_result,
            }

        # Live execution
        live_query = TradeExecuteQuery(
            symbol=payload.symbol,
            interval=payload.interval,
            candles_limit=payload.candles_limit,
            rr_target=payload.rr_target,
            account_balance=payload.account_balance,
            risk_percent=payload.risk_percent,
            leverage=payload.leverage,
            idempotency_key=payload.idempotency_key,
            confirm_live=payload.confirm_live,
        )

        live_result = await build_execute_live(live_query)
        logger.info(
            "trade_decision_execute_live_completed symbol=%s interval=%s idempotency_key=%s",
            payload.symbol,
            payload.interval,
            payload.idempotency_key,
        )

        return {
            "exchange": "BingX",
            "mode": "live",
            "plan": plan.get("data", plan),
            "preview": preview.get("data", preview),
            "execution": live_result,
        }
    except ValueError as exc:
        logger.warning(
            "trade_decision_execute_invalid symbol=%s interval=%s detail=%s",
            payload.symbol,
            payload.interval,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/preview", response_model=TradePreviewResponse)
async def trade_preview(query: TradePreviewQuery):
    try:
        return await build_trade_preview(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.post("/trailing-stop/preview", response_model=TrailingStopPreviewResponse)
async def trailing_stop_preview(query: TrailingStopPreviewQuery):
    try:
        return await build_trailing_stop_preview(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
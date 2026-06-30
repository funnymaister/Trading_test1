import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request
from core.limiter import limiter

from schemas.market import (
    CandidatesQuery,
    CandidatesResponse,
    CandlesQuery,
    CandlesResponse,
    IndicatorsQuery,
    IndicatorsResponse,
    MoversQuery,
    MoversResponse,
    ShortlistQuery,
    ShortlistResponse,
    SignalQuery,
    SignalResponse,
)

from services.market_service import (
    build_movers,
    build_shortlist,
    fetch_candidates,
    fetch_candles,
    fetch_contracts,
    fetch_indicators,
    fetch_signal,
    fetch_tickers_24h,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


@router.get(
    "/health",
    summary="Market router health",
    description="Returns a lightweight health response for the market router.",
    responses={
        200: {
            "description": "Market router is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            },
        }
    },
)
async def market_health() -> dict[str, str]:
    logger.info("market_health_requested")
    return {"status": "ok"}


@router.get(
    "/candidates",
    response_model=CandidatesResponse,
    summary="Get market candidates",
    description="Builds candidate symbols for further market evaluation based on interval and ranking parameters.",
)
async def market_candidates(
    interval: Literal["5m", "15m", "1h"] = Query(default="5m", description="Timeframe used for candidate scoring."),
    limit: Annotated[int, Query(ge=1, le=20, description="Maximum number of candidate symbols to inspect.")] = 20,
    candles_limit: Annotated[int, Query(ge=50, le=1000, description="Number of candles used for calculations.")] = 200,
    top_k: Annotated[int, Query(ge=1, le=20, description="Number of top-ranked candidates to return.")] = 5,
) -> CandidatesResponse:
    logger.info(
        "market_candidates_requested interval=%s limit=%s candles_limit=%s top_k=%s",
        interval,
        limit,
        candles_limit,
        top_k,
    )
    query = CandidatesQuery(
        interval=interval,
        limit=limit,
        candles_limit=candles_limit,
        top_k=top_k,
    )
    result = await fetch_candidates(query)
    items_count = len(result.items) if hasattr(result, "items") else "unknown"
    logger.info(
        "market_candidates_loaded interval=%s items_count=%s",
        interval,
        items_count,
    )
    return result


@router.get(
    "/signals",
    response_model=SignalResponse,
    summary="Get market signal",
    description="Returns a computed trading signal for a symbol and interval.",
)
async def market_signals(
    symbol: Annotated[str, Query(min_length=3, max_length=30, description="Market symbol, for example BTC-USDT.")],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m", description="Signal timeframe."),
    limit: Annotated[int, Query(ge=50, le=1000, description="Number of candles used to compute the signal.")] = 200,
) -> SignalResponse:
    logger.info(
        "market_signal_requested symbol=%s interval=%s limit=%s",
        symbol,
        interval,
        limit,
    )
    query = SignalQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    result = await fetch_signal(query)
    logger.info(
        "market_signal_loaded symbol=%s interval=%s",
        symbol,
        interval,
    )
    return result


@router.get(
    "/candles",
    response_model=CandlesResponse,
    summary="Get historical candles",
    description="Returns historical market candles for a symbol and interval.",
)
async def market_candles(
    symbol: Annotated[str, Query(min_length=3, max_length=30, description="Market symbol, for example BTC-USDT.")],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m", description="Candlestick timeframe."),
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum number of candles to return.")] = 100,
) -> CandlesResponse:
    logger.info(
        "market_candles_requested symbol=%s interval=%s limit=%s",
        symbol,
        interval,
        limit,
    )
    query = CandlesQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    result = await fetch_candles(query)
    logger.info(
        "market_candles_loaded symbol=%s interval=%s",
        symbol,
        interval,
    )
    return result


@router.get(
    "/indicators",
    response_model=IndicatorsResponse,
    summary="Get market indicators",
    description="Returns derived technical indicators for a symbol and interval.",
)
async def market_indicators(
    symbol: Annotated[str, Query(min_length=3, max_length=30, description="Market symbol, for example BTC-USDT.")],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m", description="Indicator timeframe."),
    limit: Annotated[int, Query(ge=50, le=1000, description="Number of candles used for indicator calculations.")] = 200,
) -> IndicatorsResponse:
    logger.info(
        "market_indicators_requested symbol=%s interval=%s limit=%s",
        symbol,
        interval,
        limit,
    )
    query = IndicatorsQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    result = await fetch_indicators(query)
    logger.info(
        "market_indicators_loaded symbol=%s interval=%s",
        symbol,
        interval,
    )
    return result


@router.get(
    "/shortlist",
    response_model=ShortlistResponse,
    summary="Get market shortlist",
    description="Returns a filtered shortlist of tradeable contracts based on quote asset and trading filters.",
    responses={
        200: {
            "description": "Filtered shortlist of contracts",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "symbol": "BTC-USDT",
                                "quote_asset": "USDT"
                            }
                        ]
                    }
                }
            },
        }
    },
)
@limiter.limit("10/minute")
async def get_shortlist(
    request: Request,
    quote_asset: Annotated[str, Query(min_length=3, max_length=10, description="Quote asset filter, usually USDT.")] = "USDT",
    only_trading: bool = Query(default=True, description="Return only actively trading contracts."),
    only_api_trading: bool = Query(default=True, description="Return only contracts available for API trading."),
    min_notional: Annotated[float | None, Query(ge=0, description="Optional minimum notional filter.")] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of shortlisted contracts to return.")] = 30,
) -> ShortlistResponse:
    logger.info(
        "market_shortlist_requested quote_asset=%s only_trading=%s only_api_trading=%s min_notional=%s limit=%s",
        quote_asset,
        only_trading,
        only_api_trading,
        min_notional,
        limit,
    )
    query = ShortlistQuery(
        quote_asset=quote_asset,
        only_trading=only_trading,
        only_api_trading=only_api_trading,
        min_notional=min_notional,
        limit=limit,
    )
    contracts = await fetch_contracts()
    result = build_shortlist(contracts, query)
    items_count = len(result.items) if hasattr(result, "items") else "unknown"
    logger.info(
        "market_shortlist_built quote_asset=%s items_count=%s",
        quote_asset,
        items_count,
    )
    return result


@router.get(
    "/movers",
    response_model=MoversResponse,
    summary="Get top market movers",
    description="Returns ranked gainers or movers from 24h ticker data.",
)
async def market_movers(
    quote_asset: str = Query(default="USDT", description="Quote asset filter, usually USDT."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of movers to return."),
    sort: str = Query(default="gainers", description="Sorting mode, for example gainers."),
) -> MoversResponse:
    logger.info(
        "market_movers_requested quote_asset=%s limit=%s sort=%s",
        quote_asset,
        limit,
        sort,
    )
    query = MoversQuery(
        quote_asset=quote_asset,
        limit=limit,
        sort=sort,
    )
    tickers = await fetch_tickers_24h()
    result = build_movers(tickers, query)
    items_count = len(result.items) if hasattr(result, "items") else "unknown"
    logger.info(
        "market_movers_built quote_asset=%s sort=%s items_count=%s",
        quote_asset,
        sort,
        items_count,
    )
    return result
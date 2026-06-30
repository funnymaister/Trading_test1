from typing import Annotated, Literal

from core.limiter import limiter

from fastapi import APIRouter, Query, Request

from schemas.market import (
    CandidateItem,
    CandidatesQuery,
    CandidatesResponse,
    CandlesQuery,
    CandlesResponse,
    IndicatorsQuery,
    IndicatorsResponse,
    MoversQuery,
    MoversResponse,
    ScannerQuery,
    ScannerResponse,
    ShortlistQuery,
    ShortlistResponse,
    SignalQuery,
    SignalResponse,
)

from services.market_service import (
    build_movers,
    build_shortlist,
    fetch_candles,
    fetch_contracts,
    fetch_tickers_24h,
    fetch_signal,
    fetch_signal_scanner,
    fetch_candidates,
)

from schemas.market import (
    CandlesQuery,
    CandlesResponse,
    MoversQuery,
    MoversResponse,
    ShortlistQuery,
    ShortlistResponse,
)


router = APIRouter(prefix="/market", tags=["market"])


@router.get("/market/shortlist")
@limiter.limit("10/minute")
async def get_shortlist(request: Request):
    ...

@router.get("/candidates", response_model=CandidatesResponse)
async def market_candidates(
    interval: Literal["5m", "15m", "1h"] = Query(default="5m"),
    limit: Annotated[int, Query(ge=1, le=20)] = 20,
    candles_limit: Annotated[int, Query(ge=50, le=1000)] = 200,
    top_k: Annotated[int, Query(ge=1, le=20)] = 5,
) -> CandidatesResponse:
    query = CandidatesQuery(
        interval=interval,
        limit=limit,
        candles_limit=candles_limit,
        top_k=top_k,
    )
    return await fetch_candidates(query)


@router.get("/signals", response_model=SignalResponse)
async def market_signals(
    symbol: Annotated[str, Query(min_length=3, max_length=30)],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m"),
    limit: Annotated[int, Query(ge=50, le=1000)] = 200,
) -> SignalResponse:
    query = SignalQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    return await fetch_signal(query)


@router.get("/health")
async def market_health() -> dict[str, str]:
    return {"status": "ok"}

@router.get("/candles", response_model=CandlesResponse)
async def market_candles(
    symbol: Annotated[str, Query(min_length=3, max_length=30)],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m"),
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> CandlesResponse:
    query = CandlesQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    return await fetch_candles(query)

@router.get("/indicators", response_model=IndicatorsResponse)
async def market_indicators(
    symbol: Annotated[str, Query(min_length=3, max_length=30)],
    interval: Literal["5m", "15m", "1h"] = Query(default="5m"),
    limit: Annotated[int, Query(ge=50, le=1000)] = 200,
) -> IndicatorsResponse:
    query = IndicatorsQuery(
        symbol=symbol,
        interval=interval,
        limit=limit,
    )
    return await fetch_indicators(query)

@router.get("/shortlist", response_model=ShortlistResponse)
async def get_shortlist(
    quote_asset: Annotated[str, Query(min_length=3, max_length=10)] = "USDT",
    only_trading: bool = True,
    only_api_trading: bool = True,
    min_notional: Annotated[float | None, Query(ge=0)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
) -> ShortlistResponse:
    query = ShortlistQuery(
        quote_asset=quote_asset,
        only_trading=only_trading,
        only_api_trading=only_api_trading,
        min_notional=min_notional,
        limit=limit,
    )
    contracts = await fetch_contracts()
    return build_shortlist(contracts, query)


@router.get("/movers", response_model=MoversResponse)
async def market_movers(
    quote_asset: str = Query(default="USDT"),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="gainers"),
) -> MoversResponse:
    query = MoversQuery(
        quote_asset=quote_asset,
        limit=limit,
        sort=sort,
    )
    tickers = await fetch_tickers_24h()
    return build_movers(tickers, query)
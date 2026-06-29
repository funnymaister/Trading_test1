from typing import Annotated

from fastapi import APIRouter, Query

from schemas.market import ShortlistQuery, ShortlistResponse
from services.market_service import build_shortlist, fetch_contracts

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/health")
async def market_health() -> dict[str, str]:
    return {"status": "ok"}


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
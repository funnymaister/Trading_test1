import httpx
from fastapi import Request

from services.market_service import MarketService


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_market_service(request: Request) -> MarketService:
    http_client = get_http_client(request)
    return MarketService(
        http_client=http_client,
        app_state=request.app.state,
    )
from __future__ import annotations

from typing import Any

import httpx

from core.config import get_settings

settings = get_settings()


class BingXMarketClient:
    def __init__(self) -> None:
        self.base_url = settings.bingx_base_url.rstrip("/")
        self.timeout = settings.bingx_timeout_seconds

    async def get_24h_tickers(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/openApi/spot/v1/ticker/24hr"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()

        data = payload.get("data", [])
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []


bingx_market_client = BingXMarketClient()
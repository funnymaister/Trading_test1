from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from core.config import get_settings

settings = get_settings()


class BingXExecutionService:
    def __init__(self) -> None:
        self.base_url = settings.bingx_base_url.rstrip("/")
        self.api_key = settings.bingx_api_key
        self.api_secret = settings.bingx_api_secret
        self.recv_window = settings.bingx_recv_window
        self.timeout = settings.bingx_timeout_seconds

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def _request(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params.copy() if params else {}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self.recv_window

        query_string = urlencode(params)
        signature = self._sign(query_string)
        url = f"{self.base_url}{path}?{query_string}&signature={signature}"

        headers = {
            "X-BX-APIKEY": self.api_key,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method=method, url=url, headers=headers)
            response.raise_for_status()
            return response.json()

    async def place_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        leverage: int,
        position_side: str = "BOTH",
    ) -> dict[str, Any]:
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
            "leverage": leverage,
            "positionSide": position_side,
        }
        return await self._request(
            method="POST",
            path="/openApi/swap/v2/trade/order",
            params=params,
        )

    async def get_open_orders(self, *, symbol: str | None = None) -> dict[str, Any]:
        params = {"symbol": symbol} if symbol else None
        return await self._request(
            method="GET",
            path="/openApi/swap/v2/trade/openOrders",
            params=params,
        )

    async def get_positions(self, *, symbol: str | None = None) -> dict[str, Any]:
        params = {"symbol": symbol} if symbol else None
        return await self._request(
            method="GET",
            path="/openApi/swap/v2/user/positions",
            params=params,
        )

    async def place_market_close_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        position_side: str = "BOTH",
    ) -> dict[str, Any]:
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
            "positionSide": position_side,
        }
        return await self._request(
            method="POST",
            path="/openApi/swap/v2/trade/order",
            params=params,
        )


bingx_execution_service = BingXExecutionService()
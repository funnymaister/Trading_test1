from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ShortlistQuery(BaseModel):
    quote_asset: str = Field(default="USDT")
    only_trading: bool = Field(default=True)
    only_api_trading: bool = Field(default=True)
    min_notional: float | None = Field(default=None, ge=0)
    limit: int = Field(default=30, ge=1, le=200)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_quote_asset(self) -> str:
        return self.quote_asset.upper()


class MarketSymbol(BaseModel):
    symbol: str
    status: str | None = None
    quote_asset: str | None = None
    min_notional: float | None = None
    tick_size: str | None = None
    step_size: str | None = None
    api_buy: bool | None = None
    api_sell: bool | None = None


class ShortlistResponse(BaseModel):
    exchange: str
    total_symbols: int
    filtered_symbols: int
    filters: dict
    items: list[MarketSymbol]


class MoversQuery(BaseModel):
    quote_asset: str = Field(default="USDT")
    limit: int = Field(default=20, ge=1, le=100)
    sort: Literal["gainers", "losers"] = "gainers"

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_quote_asset(self) -> str:
        return self.quote_asset.upper()


class MarketMover(BaseModel):
    symbol: str
    quote_asset: str | None = None
    last_price: float | None = None
    price_change_percent: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    volume: float | None = None


class MoversResponse(BaseModel):
    exchange: str
    total_symbols: int
    filtered_symbols: int
    filters: dict
    items: list[MarketMover]


class CandlesQuery(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    interval: Literal["5m", "15m", "1h"] = "5m"
    limit: int = Field(default=100, ge=1, le=500)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class Candle(BaseModel):
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandlesResponse(BaseModel):
    exchange: str
    symbol: str
    interval: str
    count: int
    items: list[Candle]


class IndicatorsQuery(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    interval: Literal["5m", "15m", "1h"] = "5m"
    limit: int = Field(default=200, ge=50, le=1000)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class IndicatorSnapshot(BaseModel):
    symbol: str
    interval: str
    candles_count: int
    last_close: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    rsi_14: float | None = None


class IndicatorsResponse(BaseModel):
    exchange: str
    data: IndicatorSnapshot


class SignalQuery(BaseModel):
    symbol: str = Field(min_length=3, max_length=30)
    interval: Literal["5m", "15m", "1h"] = "5m"
    limit: int = Field(default=200, ge=50, le=1000)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class SignalSnapshot(BaseModel):
    symbol: str
    interval: str
    signal: Literal["long", "short", "neutral"]
    reason: str
    candles_count: int
    last_close: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    rsi_14: float | None = None


class SignalResponse(BaseModel):
    exchange: str
    data: SignalSnapshot

class ScannerQuery(BaseModel):
        interval: Literal["5m", "15m", "1h"] = "5m"
        limit: int = Field(default=20, ge=1, le=20)
        candles_limit: int = Field(default=200, ge=50, le=1000)

        model_config = ConfigDict(str_strip_whitespace=True)

class ScannerResponse(BaseModel):
        exchange: str
        interval: str
        scanned: int
        signals_found: int
        items: list[SignalSnapshot]

class ScannerQuery(BaseModel):
        interval: Literal["5m", "15m", "1h"] = "5m"
        limit: int = Field(default=20, ge=1, le=20)
        candles_limit: int = Field(default=200, ge=50, le=1000)

        model_config = ConfigDict(str_strip_whitespace=True)

class ScannerResponse(BaseModel):
        exchange: str
        interval: str
        scanned: int
        signals_found: int
        items: list[SignalSnapshot]

class CandidateItem(BaseModel):
            symbol: str
            interval: str
            signal: Literal["long", "short"]
            reason: str
            score: float
            candles_count: int
            last_close: float | None = None
            ema_20: float | None = None
            ema_50: float | None = None
            rsi_14: float | None = None

class CandidatesQuery(BaseModel):
            interval: Literal["5m", "15m", "1h"] = "5m"
            limit: int = Field(default=20, ge=1, le=20)
            candles_limit: int = Field(default=200, ge=50, le=1000)
            top_k: int = Field(default=5, ge=1, le=20)

            model_config = ConfigDict(str_strip_whitespace=True)

class CandidatesResponse(BaseModel):
            exchange: str
            interval: str
            scanned: int
            candidates_found: int
            items: list[CandidateItem]
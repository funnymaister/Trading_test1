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
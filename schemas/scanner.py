from pydantic import BaseModel


class TopMoverItem(BaseModel):
    symbol: str
    price_change_percent: float
    last_price: float | None = None
    quote_volume: float | None = None


class TopMoversResponse(BaseModel):
    exchange: str
    updated_at: str | None = None
    count: int
    items: list[TopMoverItem]
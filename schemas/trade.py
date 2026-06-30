from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from typing import Any
from pydantic import BaseModel

AllowedInterval = Literal["5m", "15m", "1h"]


class TradePlanQuery(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    interval: AllowedInterval = "5m"
    candles_limit: int = Field(default=200, ge=50, le=1000)
    rr_target: float = Field(default=2.0, ge=1.0, le=10.0)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class TradePlanData(BaseModel):
    symbol: str
    interval: str
    side: str
    signal: str
    entry_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    reason: str


class TradePlanResponse(BaseModel):
    exchange: str
    data: TradePlanData


class TradePreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    interval: AllowedInterval = "5m"
    candles_limit: int = Field(default=200, ge=50, le=1000)
    rr_target: float = Field(default=2.0, ge=1.0, le=10.0)
    account_balance: float = Field(default=1000.0, ge=10.0, le=1_000_000.0)
    risk_percent: float = Field(default=1.0, ge=0.1, le=5.0)
    leverage: int = Field(default=5, ge=1, le=50)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class TradePreviewData(BaseModel):
    symbol: str
    interval: str
    side: str
    signal: str
    entry_type: str
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    account_balance: float
    risk_percent: float
    risk_amount_usdt: float
    position_size_units: float
    position_notional_usdt: float
    required_margin_usdt: float
    leverage: int
    reason: str


class TradePreviewResponse(BaseModel):
    exchange: str
    data: TradePreviewData


class TradeExecuteDryRunQuery(TradePreviewQuery):
    pass


class ExecuteDryRunOrder(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    leverage: int
    entry_price: float
    stop_loss: float
    take_profit: float
    reduce_only: bool = False


class ExecuteDryRunResponse(BaseModel):
    exchange: str
    dry_run: bool = True
    message: str
    order: ExecuteDryRunOrder


class TradeExecuteQuery(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    interval: AllowedInterval
    candles_limit: int = Field(..., ge=50, le=1000)
    rr_target: float = Field(..., ge=1.0, le=10.0)
    account_balance: float = Field(..., ge=10.0, le=1_000_000.0)
    risk_percent: float = Field(..., gt=0.0, lt=5.0)
    leverage: int = Field(..., ge=1, lt=50)
    confirm_live: bool
    idempotency_key: str = Field(..., min_length=8, max_length=128)

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class TradeExecuteRequest(TradeExecuteQuery):
    pass


class TradeExecutionRequest(TradeExecuteQuery):
    pass


class TradeExecuteAttempt(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    leverage: int
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TradeExecutionResponse(BaseModel):
    exchange: str
    live_sent: bool
    status: str
    idempotency_key: str
    message: str
    attempt: TradeExecuteAttempt


class ClosePositionQuery(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=30)
    confirm_close: bool

    model_config = ConfigDict(str_strip_whitespace=True)

    def normalized_symbol(self) -> str:
        return self.symbol.upper()


class ClosePositionRequest(ClosePositionQuery):
    pass


class ClosePositionAttempt(BaseModel):
    symbol: str
    side: str
    order_type: str
    quantity: float
    position_side: str


class ClosePositionResponse(BaseModel):
    exchange: str
    live_sent: bool
    message: str
    attempt: ClosePositionAttempt


class PositionItem(BaseModel):
    symbol: str
    position_side: Optional[str] = None
    side: Optional[str] = None
    quantity: Optional[float] = None
    entry_price: Optional[float] = None
    mark_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    liquidation_price: Optional[float] = None
    leverage: Optional[int] = None


class PositionsResponse(BaseModel):
    exchange: str
    items: list[PositionItem]


class OpenOrderItem(BaseModel):
    order_id: str
    symbol: str
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[float] = None


class OpenOrdersResponse(BaseModel):
    exchange: str
    items: list[OpenOrderItem]

class ExecutionLogEntry(BaseModel):
        exchange: str
        live_sent: bool
        status: str
        idempotency_key: str | None = None
        message: str
        attempt: dict[str, Any]
        exchange_response: Any | None = None

class ExecutionLogResponse(BaseModel):
        items: list[ExecutionLogEntry]
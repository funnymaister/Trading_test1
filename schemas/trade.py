from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from typing import Any

AllowedInterval = Literal["5m", "15m", "1h"]


class BreakevenPreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    current_stop_loss: float = Field(..., gt=0)
    activation_rr: float = Field(..., gt=0, le=10)
    risk_per_unit: float = Field(..., gt=0)
    buffer_percent: float = Field(0.0, ge=0, le=5)


class BreakevenPreviewResponse(BaseModel):
    exchange: str
    data: dict

class PartialClosePreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    position_size_units: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    close_percent: float = Field(..., gt=0, le=100)


class PartialClosePreviewResponse(BaseModel):
    exchange: str
    data: dict

class TradePreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    interval: str = Field(..., pattern="^(1m|5m|15m|1h|4h|1d)$")
    candles_limit: int = Field(..., ge=50, le=1000)
    rr_target: float = Field(..., ge=1.0, le=10.0)
    account_balance: float = Field(..., gt=0)
    risk_percent: float = Field(..., gt=0, le=100)
    leverage: int = Field(..., ge=1, le=125)


class TradePreviewResponse(BaseModel):
    exchange: str
    data: dict


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



class TradeDecisionData(BaseModel):
            plan: dict[str, Any]
            preview: dict[str, Any]

class TradeDecisionResponse(BaseModel):
            exchange: str
            data: TradeDecisionData

class TradeDecisionExecuteQuery(BaseModel):
                symbol: str
                interval: AllowedInterval
                candles_limit: int
                rr_target: float
                account_balance: float
                risk_percent: float
                leverage: int
                idempotency_key: str
                confirm_live: bool = False
                dry_run: bool = True


class TrailingStopPreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    current_stop_loss: float = Field(..., gt=0)
    trail_distance_percent: float = Field(..., gt=0, le=20)
    activation_percent: float = Field(..., ge=0, le=20)


class TrailingStopPreviewResponse(BaseModel):
    exchange: str
    data: dict
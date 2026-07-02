from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from typing import Any, Literal

AllowedInterval = Literal["5m", "15m", "1h"]


class TradeJournalEntryResponse(BaseModel):
    exchange: str
    data: dict


class TradeJournalListResponse(BaseModel):
    exchange: str
    count: int
    data: list[dict]

class TradeJournalSaveQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    outcome: Literal["win", "loss", "breakeven"]
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: float = Field(..., gt=0)
    exit_price: float = Field(..., gt=0)
    position_size_units: float = Field(..., gt=0)
    fees_usdt: float = Field(0.0, ge=0)
    r_multiple: float
    net_pnl_usdt: float
    note: str | None = None


class TradeJournalSaveResponse(BaseModel):
    exchange: str
    data: dict

class TradeStatsItem(BaseModel):
    outcome: Literal["win", "loss", "breakeven"]
    r_multiple: float
    net_pnl_usdt: float


class TradeStatsQuery(BaseModel):
    trades: list[TradeStatsItem] = Field(..., min_length=1)


class TradeStatsResponse(BaseModel):
    total_trades: int
    win_rate_percent: float
    loss_rate_percent: float
    breakeven_rate_percent: float
    avg_r_multiple: float
    avg_win_r: float | None
    avg_loss_r: float | None
    expectancy_r: float
    total_net_pnl_usdt: float
    avg_net_pnl_usdt: float

class TradeJournalPreviewQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    take_profit: float = Field(..., gt=0)
    exit_price: float = Field(..., gt=0)
    position_size_units: float = Field(..., gt=0)
    fees_usdt: float = Field(0.0, ge=0)
    note: str | None = None


class TradeJournalPreviewResponse(BaseModel):
    exchange: str
    data: dict

class PositionExitPlanQuery(BaseModel):
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    entry_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    current_stop_loss: float = Field(..., gt=0)
    position_size_units: float = Field(..., gt=0)
    partial_close_percent: float = Field(..., gt=0, le=100)
    breakeven_activation_rr: float = Field(..., gt=0, le=10)
    risk_per_unit: float = Field(..., gt=0)
    trailing_activation_percent: float = Field(..., ge=0, le=20)
    trailing_distance_percent: float = Field(..., gt=0, le=20)


class PositionExitPlanResponse(BaseModel):
    exchange: str
    data: dict

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
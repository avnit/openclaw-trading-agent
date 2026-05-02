from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


@dataclass
class Account:
    account_id: str
    account_number: str
    account_type: str
    buying_power: float
    cash: float
    portfolio_value: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Quote:
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    change: float
    change_pct: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderRequest:
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: TimeInForce = TimeInForce.DAY


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str
    quantity: float
    filled_quantity: float
    order_type: str
    status: str
    limit_price: float | None
    stop_price: float | None
    average_fill_price: float | None
    created_at: str
    raw: dict[str, Any] = field(default_factory=dict)

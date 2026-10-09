from dataclasses import dataclass

from matching_engine.order_book.order import OrderType, Side, TimeInForce
from matching_engine.order_book.trade import Trade

# Pedidos (o que chega no balcão)

@dataclass(frozen=True)
class NewOrder:
    instrument: str
    order_id: str
    client_order_id: str
    side: Side
    order_type: OrderType
    quantity: int
    price: int | None = None
    time_in_force: TimeInForce = TimeInForce.GTC

@dataclass(frozen=True)
class CancelOrder:
    instrument: str
    order_id: str

Command = NewOrder | CancelOrder

# Avisos (o que a secretária anuncia depois de atender)

@dataclass(frozen=True)
class OrderAccepted:
    instrument: str
    sequence: int
    order_id: str

@dataclass(frozen=True)
class OrderRejected:
    insrtument: str
    sequence: int
    order_id: str
    reason: str

@dataclass(frozen=True)
class TradeExecuted:
    instrument: str
    sequence: int
    trade: Trade

@dataclass(frozen=True)
class OrderCancelled:
    instrument: str
    sequence: int
    order_id: str
    remaining_quantity: int

@dataclass(frozen=True)
class OrderExpired:
    instrument: str
    sequence: int
    order_id: str
    remaing_quantity: int

Event = OrderAccepted | OrderRejected | TradeExecuted | OrderCancelled | OrderExpired

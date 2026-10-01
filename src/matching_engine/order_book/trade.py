
from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:

    trade_id: int
    instrument: str
    buy_order_id: str
    sell_order_id: str
    price: int
    quantity: int

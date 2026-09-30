from dataclasses import dataclass, field
from enum import StrEnum


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(StrEnum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


@dataclass(eq=False)
class Order:
    order_id: str
    client_order_id: str
    side: Side
    order_type: OrderType
    quantity: int
    price: int | None = None
    time_in_force: TimeInForce = TimeInForce.GTC
    remaining_quantity: int = field(init=False)

    def __post_init__(self) -> None:
        self._validate()
        self.remaining_quantity = self.quantity

    def _validate(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if self.order_type is OrderType.LIMIT:
            self._validate_limit()
        else:
            self._validate_market()

    def _validate_limit(self) -> None:
        if self.price is None or self.price <= 0:
            raise ValueError("limit orders require a positive price")

    def _validate_market(self) -> None:
        if self.price is not None:
            raise ValueError("market orders must not have a price")
        if self.time_in_force is TimeInForce.GTC:
            raise ValueError("market orders cannot rest in the book; use IOC or FOK")

    @property
    def is_filled(self) -> bool:
        return self.remaining_quantity == 0

    def fill(self, quantity: int) -> None:
        """Reduce remaining_quantity after a partial or full match."""
        if quantity <= 0:
            raise ValueError("fill quantity must be greater than zero")
        if quantity > self.remaining_quantity:
            raise ValueError("fill quantity exceeds remaining quantity")
        self.remaining_quantity -= quantity
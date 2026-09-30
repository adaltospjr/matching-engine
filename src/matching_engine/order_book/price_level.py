"""A price level: all resting orders at one specific price, FIFO."""

from collections import OrderedDict

from matching_engine.order_book.order import Order


class PriceLevel:
    """Orders resting at a single price, ordered by arrival (time priority).

    Internally backed by an OrderedDict keyed by order_id: O(1) insertion,
    O(1) cancellation of any order regardless of position, and O(1) access
    to the oldest order (the next one eligible to match).
    """

    def __init__(self, price: int) -> None:
        self.price = price
        self._orders: OrderedDict[str, Order] = OrderedDict()
        self.total_quantity: int = 0

    def add(self, order: Order) -> None:
        """Append an order to the back of the queue."""
        if order.price != self.price:
            raise ValueError(
                f"order price {order.price} does not match level price {self.price}"
            )
        if order.order_id in self._orders:
            raise ValueError(f"order {order.order_id} already exists in this level")

        self._orders[order.order_id] = order
        self.total_quantity += order.remaining_quantity

    def remove(self, order_id: str) -> Order:
        """Cancel and return a specific order, regardless of its position."""
        order = self._orders.pop(order_id)
        self.total_quantity -= order.remaining_quantity
        return order

    def peek(self) -> Order | None:
        """Return the oldest order without removing it. None if the level is empty."""
        if not self._orders:
            return None
        return next(iter(self._orders.values()))

    def apply_fill(self, order_id: str, quantity: int) -> None:
        """Reduce an order's remaining quantity; drop it if fully filled."""
        order = self._orders[order_id]
        order.fill(quantity)
        self.total_quantity -= quantity
        if order.is_filled:
            del self._orders[order_id]

    @property
    def is_empty(self) -> bool:
        return not self._orders

    def __len__(self) -> int:
        return len(self._orders)
from matching_engine.order_book.book_side import BookSide
from matching_engine.order_book.order import Order, Side


class OrderBook:
    """Order book for one instrument, composed of a bid side and an ask side."""

    def __init__(self, instrument: str) -> None:
        self.instrument = instrument
        self.bids = BookSide(Side.BUY)
        self.asks = BookSide(Side.SELL)
        self._order_sides: dict[str, Side] = {}

    def _side_for(self, side: Side) -> BookSide:
        return self.bids if side is Side.BUY else self.asks

    def add_order(self, order: Order) -> None:
        if order.order_id in self._order_sides:
            raise ValueError(f"order {order.order_id} already exists in the book")
        self._side_for(order.side).add_order(order)
        self._order_sides[order.order_id] = order.side

    def cancel_order(self, order_id: str) -> Order:
        side = self._order_sides.pop(order_id)
        return self._side_for(side).cancel_order(order_id)

    def apply_fill(self, order_id: str, quantity: int) -> Order:
        side = self._order_sides[order_id]
        order = self._side_for(side).apply_fill(order_id, quantity)
        if order.is_filled:
            self._order_sides.pop(order_id, None)
        return order

    @property
    def best_bid(self) -> int | None:
        return self.bids.best_price

    @property
    def best_ask(self) -> int | None:
        return self.asks.best_price

    @property
    def spread(self) -> int | None:
        if self.best_bid is None or self.best_ask is None:
            return None
        return self.best_ask - self.best_bid
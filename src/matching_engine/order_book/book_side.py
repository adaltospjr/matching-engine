import heapq

from matching_engine.order_book.order import Order, Side
from matching_engine.order_book.price_level import PriceLevel


class BookSide:

    def __init__(self, side: Side) -> None:
        self.side = side
        self._sign = -1 if side is Side.BUY else 1
        self._levels: dict[int, PriceLevel] = {}
        self._price_heap: list[int] = []
        self._order_prices: dict[str, int] = {}

    def add_order(self, order: Order) -> None:
        price = order.price
        level = self._levels.get(price)
        if level is None:
            level = PriceLevel(price)
            self._levels[price] = level
            heapq.heappush(self._price_heap, self._sign * price)
        level.add(order)
        self._order_prices[order.order_id] = price

    def cancel_order(self, order_id: str) -> Order:
        price = self._order_prices.pop(order_id)
        level = self._levels[price]
        order = level.remove(order_id)
        if level.is_empty:
            del self._levels[price]
        return order

    def apply_fill(self, order_id: str, quantity: int) -> Order:
        price = self._order_prices[order_id]
        level = self._levels[price]
        order = level.apply_fill(order_id, quantity)
        if order.is_filled:
            self._order_prices.pop(order_id, None)
            if level.is_empty:
                del self._levels[price]
        return order

    def best_level(self) -> PriceLevel | None:
        """Return the level at the best price, skipping stale heap entries."""
        while self._price_heap:
            candidate_price = self._sign * self._price_heap[0]
            level = self._levels.get(candidate_price)
            if level is not None and not level.is_empty:
                return level
            heapq.heappop(self._price_heap)
        return None

    @property
    def best_price(self) -> int | None:
        level = self.best_level()
        return level.price if level else None

    def __len__(self) -> int:
        return len(self._levels)
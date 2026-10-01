"""The order book for a single instrument: bid side + ask side + matching."""

import itertools

from matching_engine.order_book.book_side import BookSide
from matching_engine.order_book.order import Order, OrderType, Side, TimeInForce
from matching_engine.order_book.trade import Trade


def _opposite(side: Side) -> Side:
    return Side.SELL if side is Side.BUY else Side.BUY


class OrderBook:

    def __init__(self, instrument: str) -> None:
        self.instrument = instrument
        self.bids = BookSide(Side.BUY)
        self.asks = BookSide(Side.SELL)
        self._order_sides: dict[str, Side] = {}
        self._trade_ids = itertools.count(1)

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

    def submit(self, order: Order) -> list[Trade]:

        opposite = self._side_for(_opposite(order.side))

        if order.time_in_force is TimeInForce.FOK and not self._can_fully_fill(order, opposite):
            return []

        trades = self._match_against(order, opposite)

        if order.remaining_quantity > 0 and order.time_in_force is TimeInForce.GTC:
            self.add_order(order)

        return trades

    def _match_against(self, order: Order, opposite: BookSide) -> list[Trade]:
        trades: list[Trade] = []

        while order.remaining_quantity > 0:
            level = opposite.best_level()
            if level is None:
                break
            if order.order_type is OrderType.LIMIT and not self._crosses(order, level.price):
                break

            resting_order = level.peek()
            match_quantity = min(order.remaining_quantity, resting_order.remaining_quantity)

            order.fill(match_quantity)
            filled_resting = opposite.apply_fill(resting_order.order_id, match_quantity)
            if filled_resting.is_filled:
                self._order_sides.pop(filled_resting.order_id, None)

            trades.append(self._build_trade(order, resting_order, match_quantity))

        return trades

    def _build_trade(self, incoming: Order, resting: Order, quantity: int) -> Trade:
        buy_order_id = incoming.order_id if incoming.side is Side.BUY else resting.order_id
        sell_order_id = resting.order_id if incoming.side is Side.BUY else incoming.order_id
        return Trade(
            trade_id=next(self._trade_ids),
            instrument=self.instrument,
            buy_order_id=buy_order_id,
            sell_order_id=sell_order_id,
            price=resting.price,
            quantity=quantity,
        )

    def _crosses(self, order: Order, level_price: int) -> bool:
        if order.order_type is OrderType.MARKET:
            return True
        if order.side is Side.BUY:
            return order.price >= level_price
        return order.price <= level_price

    def _can_fully_fill(self, order: Order, opposite: BookSide) -> bool:
        remaining = order.quantity
        for level in opposite.iter_levels_best_first():
            if order.order_type is OrderType.LIMIT and not self._crosses(order, level.price):
                break
            remaining -= level.total_quantity
            if remaining <= 0:
                return True
        return remaining <= 0

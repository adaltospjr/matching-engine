from matching_engine.engine.messages import (
    CancelOrder,
    Command,
    Event,
    NewOrder,
    OrderAccepted,
    OrderCancelled,
    OrderExpired,
    OrderRejected,
    TradeExecuted
)

from matching_engine.order_book.book import OrderBook
from matching_engine.order_book.order import Order, TimeInForce

class MatchingEngine:

    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}
        self._sequences: dict[str, int] = {}

    def handle(self, command: Command) -> list[Event]:
        if isinstance(command, NewOrder):
            return self._handle_new_order(command)
        return self._handle_cancel(command)

    def _handle_new_order(self, command: NewOrder) -> list[Event]:
        try:
            order = Order(
                order_id=command.order_id,
                client_order_id=command.client_order_id,
                side=command.side,
                order_type=command.order_type,
                quantity=command.quantity,
                price=command.price,
                time_in_force=command.time_in_force
            )
        except ValueError as error:
            return self._reject(command.instrument, command.order_id, str(error))

        book = self._book_for(command.instrument)
        if book.has_order(order.order_id):
            return self._reject(
                command.instrument,
                command.order_id,
                f"order {order.order_id} already exists in the book"
            )

        events: list[Event] = [
            OrderAccepted(
                instrument=command.instrument,
                sequence=self._next_sequence(command.instrument),
                order_id=order.order_id,
            )
        ]

        for trade in book.submit(order):
            events.append(
                TradeExecuted(
                    instrument=command.instrument,
                    sequence=self._next_sequence(command.instrument),
                    trade=trade,
                )
            )


        if order.remaining_quantity > 0 and order.time_in_force is not TimeInForce.GTC:
            events.append(
                OrderExpired(
                    instrument=command.instrument,
                    sequence=self._next_sequence(command.instrument),
                    order_id=order.order_id,
                    remaing_quantity=order.remaining_quantity,
                )
            )

        return events

    def _handle_cancel(self, command: CancelOrder) -> list[Event]:
        book = self._books.get(command.instrument)
        if book is None or not book.has_order(command.order_id):
            return self._reject(
                command.instrument,
                command.order_id,
                f"order {command.order_id} not found",
            )

        order = book.cancel_order(command.order_id)
        return [
            OrderCancelled(
                instrument=command.instrument,
                sequence=self._next_sequence(command.instrument),
                order_id=order.order_id,
                remaining_quantity=order.remaining_quantity,
            )
        ]


    def _reject(self, instrument: str, order_id: str, reason: str) -> list[Event]:
        return [
            OrderRejected(
                instrument=instrument,
                sequence=self._next_sequence(instrument),
                order_id=order_id,
                reason=reason
            )
        ]

    def _book_for(self, instrument: str) -> OrderBook:
        if instrument not in self._books:
            self._books[instrument] = OrderBook(instrument=instrument)
        return self._books[instrument]


    def _next_sequence(self, instrument: str) -> int:
        self._sequences[instrument] = self._sequences.get(instrument, 0) + 1
        return self._sequences[instrument]

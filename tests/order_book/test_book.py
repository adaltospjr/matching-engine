import pytest

from matching_engine.order_book.book import OrderBook
from matching_engine.order_book.order import Order, OrderType, Side


def make_order(order_id: str, side: Side, price: int, quantity: int = 100) -> Order:
    return Order(
        order_id=order_id,
        client_order_id=f"c-{order_id}",
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
    )


def test_new_book_has_no_best_prices():
    book = OrderBook(instrument="PETR4")
    assert book.best_bid is None
    assert book.best_ask is None
    assert book.spread is None


def test_add_order_routes_to_correct_side():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("buy1", Side.BUY, price=3200))
    book.add_order(make_order("sell1", Side.SELL, price=3300))

    assert book.best_bid == 3200
    assert book.best_ask == 3300


def test_spread_is_ask_minus_bid():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("buy1", Side.BUY, price=3200))
    book.add_order(make_order("sell1", Side.SELL, price=3300))

    assert book.spread == 100


def test_add_order_rejects_duplicate_id_across_sides():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("o1", Side.BUY, price=3200))
    with pytest.raises(ValueError, match="already exists"):
        book.add_order(make_order("o1", Side.SELL, price=3300))


def test_cancel_order_does_not_require_knowing_the_side():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("o1", Side.SELL, price=3300))

    cancelled = book.cancel_order("o1")

    assert cancelled.order_id == "o1"
    assert book.best_ask is None


def test_apply_fill_routes_to_correct_side():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("buy1", Side.BUY, price=3200, quantity=100))

    order = book.apply_fill("buy1", 60)

    assert order.remaining_quantity == 40
    assert book.best_bid == 3200  # order still resting, partially filled


def test_apply_fill_fully_removes_order_from_index():
    book = OrderBook(instrument="PETR4")
    book.add_order(make_order("buy1", Side.BUY, price=3200, quantity=100))

    book.apply_fill("buy1", 100)

    with pytest.raises(KeyError):
        book.cancel_order("buy1")  # already gone, nothing left to cancel
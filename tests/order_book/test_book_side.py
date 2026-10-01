import pytest

from matching_engine.order_book.book_side import BookSide
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


def test_empty_side_has_no_best_price():
    side = BookSide(Side.BUY)
    assert side.best_price is None
    assert side.best_level() is None


def test_bid_side_best_price_is_highest():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3200))
    side.add_order(make_order("o2", Side.BUY, price=3250))
    side.add_order(make_order("o3", Side.BUY, price=3100))

    assert side.best_price == 3250


def test_ask_side_best_price_is_lowest():
    side = BookSide(Side.SELL)
    side.add_order(make_order("o1", Side.SELL, price=3300))
    side.add_order(make_order("o2", Side.SELL, price=3250))
    side.add_order(make_order("o3", Side.SELL, price=3400))

    assert side.best_price == 3250


def test_orders_at_same_price_share_one_level():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3250, quantity=100))
    side.add_order(make_order("o2", Side.BUY, price=3250, quantity=50))

    level = side.best_level()
    assert level.total_quantity == 150
    assert len(side) == 1  # one level, two orders


def test_cancel_order_by_id_without_knowing_price():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3250))

    cancelled = side.cancel_order("o1")

    assert cancelled.order_id == "o1"
    assert side.best_price is None


def test_best_price_skips_stale_level_after_cancellation():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3250))
    side.add_order(make_order("o2", Side.BUY, price=3200))

    side.cancel_order("o1")  # empties the best level; heap keeps a stale entry

    assert side.best_price == 3200


def test_apply_partial_fill_keeps_order_at_its_level():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3250, quantity=100))

    order = side.apply_fill("o1", 40)

    assert order.remaining_quantity == 60
    assert side.best_level().total_quantity == 60


def test_apply_full_fill_removes_order_and_advances_best_price():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3250, quantity=100))
    side.add_order(make_order("o2", Side.BUY, price=3200, quantity=50))

    order = side.apply_fill("o1", 100)

    assert order.is_filled
    assert side.best_price == 3200


def test_cancel_missing_order_raises():
    side = BookSide(Side.BUY)
    with pytest.raises(KeyError):
        side.cancel_order("does-not-exist")

def test_iter_levels_best_first_orders_by_price_without_mutating_heap():
    side = BookSide(Side.BUY)
    side.add_order(make_order("o1", Side.BUY, price=3200))
    side.add_order(make_order("o2", Side.BUY, price=3250))
    side.add_order(make_order("o3", Side.BUY, price=3100))

    prices = [level.price for level in side.iter_levels_best_first()]

    assert prices == [3250, 3200, 3100]
    assert side.best_price == 3250  # heap still intact afterward
import pytest

from matching_engine.order_book.order import Order, OrderType, Side
from matching_engine.order_book.price_level import PriceLevel


def make_order(order_id: str, quantity: int = 100, price: int = 3250) -> Order:
    return Order(
        order_id=order_id,
        client_order_id=f"c-{order_id}",
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price,
    )


def test_new_level_is_empty():
    level = PriceLevel(price=3250)
    assert level.is_empty
    assert len(level) == 0
    assert level.peek() is None


def test_add_increases_total_quantity():
    level = PriceLevel(price=3250)
    level.add(make_order("o1", quantity=100))
    level.add(make_order("o2", quantity=50))
    assert level.total_quantity == 150
    assert len(level) == 2


def test_add_rejects_price_mismatch():
    level = PriceLevel(price=3250)
    with pytest.raises(ValueError, match="does not match level price"):
        level.add(make_order("o1", price=3300))


def test_add_rejects_duplicate_order_id():
    level = PriceLevel(price=3250)
    level.add(make_order("o1"))
    with pytest.raises(ValueError, match="already exists"):
        level.add(make_order("o1"))


def test_peek_returns_oldest_without_removing():
    level = PriceLevel(price=3250)
    level.add(make_order("o1"))
    level.add(make_order("o2"))

    assert level.peek().order_id == "o1"
    assert len(level) == 2  # still there, peek does not remove


def test_remove_cancels_specific_order_and_updates_total():
    level = PriceLevel(price=3250)
    level.add(make_order("o1", quantity=100))
    level.add(make_order("o2", quantity=50))

    removed = level.remove("o1")

    assert removed.order_id == "o1"
    assert level.total_quantity == 50
    assert level.peek().order_id == "o2"


def test_remove_missing_order_raises():
    level = PriceLevel(price=3250)
    with pytest.raises(KeyError):
        level.remove("does-not-exist")


def test_apply_partial_fill_keeps_order_in_queue():
    level = PriceLevel(price=3250)
    level.add(make_order("o1", quantity=100))

    level.apply_fill("o1", 40)

    assert level.total_quantity == 60
    assert len(level) == 1
    assert level.peek().remaining_quantity == 60


def test_apply_full_fill_removes_order():
    level = PriceLevel(price=3250)
    level.add(make_order("o1", quantity=100))

    level.apply_fill("o1", 100)

    assert level.is_empty
    assert level.total_quantity == 0


def test_time_priority_is_preserved_across_fills():
    level = PriceLevel(price=3250)
    level.add(make_order("o1", quantity=50))
    level.add(make_order("o2", quantity=50))

    level.apply_fill("o1", 50)  # o1 fully filled and removed

    assert level.peek().order_id == "o2"  # o2 is now the oldest
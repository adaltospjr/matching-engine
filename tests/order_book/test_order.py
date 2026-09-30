from typing import Any

import pytest

from matching_engine.order_book.order import Order, OrderType, Side, TimeInForce


def make_order(**overrides: Any) -> Order:
    """Build a valid limit order, overriding only what the test cares about."""
    defaults: dict[str, Any] = {
        "order_id": "o1",
        "client_order_id": "c1",
        "side": Side.BUY,
        "order_type": OrderType.LIMIT,
        "quantity": 100,
        "price": 3250,
    }
    return Order(**{**defaults, **overrides})


@pytest.mark.parametrize("price", [None, 0, -5])
def test_limit_order_requires_positive_price(price):
    with pytest.raises(ValueError, match="positive price"):
        make_order(price=price)


def test_market_order_rejects_price():
    with pytest.raises(ValueError, match="must not have a price"):
        make_order(order_type=OrderType.MARKET, price=3250, time_in_force=TimeInForce.IOC)


def test_market_order_cannot_rest_in_book():
    with pytest.raises(ValueError, match="cannot rest"):
        make_order(order_type=OrderType.MARKET, price=None, time_in_force=TimeInForce.GTC)


def test_market_order_with_ioc_is_valid():
    order = make_order(order_type=OrderType.MARKET, price=None, time_in_force=TimeInForce.IOC)
    assert order.price is None


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_must_be_positive(quantity):
    with pytest.raises(ValueError, match="greater than zero"):
        make_order(quantity=quantity)


def test_remaining_quantity_starts_equal_to_quantity():
    order = make_order(quantity=100)
    assert order.remaining_quantity == 100
    assert not order.is_filled


def test_fill_reduces_remaining_quantity():
    order = make_order(quantity=100)

    order.fill(40)
    assert order.remaining_quantity == 60
    assert not order.is_filled

    order.fill(60)
    assert order.remaining_quantity == 0
    assert order.is_filled


def test_fill_cannot_exceed_remaining_quantity():
    order = make_order(quantity=100)
    with pytest.raises(ValueError, match="exceeds"):
        order.fill(150)


@pytest.mark.parametrize("quantity", [0, -1])
def test_fill_quantity_must_be_positive(quantity):
    order = make_order(quantity=100)
    with pytest.raises(ValueError, match="greater than zero"):
        order.fill(quantity)
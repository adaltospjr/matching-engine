
from matching_engine.order_book.book import OrderBook
from matching_engine.order_book.order import Order, OrderType, Side, TimeInForce


def make_order(
    order_id: str,
    side: Side,
    quantity: int,
    price: int | None = None,
    order_type: OrderType = OrderType.LIMIT,
    time_in_force: TimeInForce = TimeInForce.GTC,
) -> Order:
    return Order(
        order_id=order_id,
        client_order_id=f"c-{order_id}",
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        time_in_force=time_in_force,
    )


def test_non_crossing_limit_order_rests_in_book():
    book = OrderBook(instrument="PETR4")
    trades = book.submit(make_order("buy1", Side.BUY, quantity=100, price=3200))

    assert trades == []
    assert book.best_bid == 3200


def test_crossing_limit_order_produces_a_trade():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=100, price=3250))

    trades = book.submit(make_order("buy1", Side.BUY, quantity=100, price=3250))

    assert len(trades) == 1
    trade = trades[0]
    assert trade.buy_order_id == "buy1"
    assert trade.sell_order_id == "sell1"
    assert trade.quantity == 100
    assert trade.price == 3250
    assert book.best_bid is None
    assert book.best_ask is None


def test_trade_executes_at_resting_order_price_not_incoming_price():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=100, price=3200))

    trades = book.submit(make_order("buy1", Side.BUY, quantity=100, price=3250))

    assert trades[0].price == 3200


def test_partial_match_leaves_remainder_resting():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=40, price=3250))

    trades = book.submit(make_order("buy1", Side.BUY, quantity=100, price=3250))

    assert len(trades) == 1
    assert trades[0].quantity == 40
    assert book.best_ask is None
    assert book.best_bid == 3250


def test_time_priority_fills_oldest_order_first_at_same_price():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=50, price=3250))
    book.submit(make_order("sell2", Side.SELL, quantity=50, price=3250))

    trades = book.submit(make_order("buy1", Side.BUY, quantity=50, price=3250))

    assert trades[0].sell_order_id == "sell1"


def test_order_matches_across_multiple_price_levels():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=50, price=3200))
    book.submit(make_order("sell2", Side.SELL, quantity=50, price=3250))

    trades = book.submit(make_order("buy1", Side.BUY, quantity=100, price=3250))

    assert len(trades) == 2
    assert trades[0].price == 3200
    assert trades[1].price == 3250


def test_ioc_order_discards_unfilled_remainder():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=30, price=3250))

    trades = book.submit(
        make_order("buy1", Side.BUY, quantity=100, price=3250, time_in_force=TimeInForce.IOC)
    )

    assert len(trades) == 1
    assert trades[0].quantity == 30
    assert book.best_bid is None


def test_fok_order_with_insufficient_liquidity_produces_no_trades():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=30, price=3250))

    trades = book.submit(
        make_order("buy1", Side.BUY, quantity=100, price=3250, time_in_force=TimeInForce.FOK)
    )

    assert trades == []
    assert book.best_ask == 3250
    assert book.best_bid is None


def test_fok_order_executes_fully_across_multiple_levels():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=50, price=3200))
    book.submit(make_order("sell2", Side.SELL, quantity=50, price=3250))

    trades = book.submit(
        make_order("buy1", Side.BUY, quantity=100, price=3250, time_in_force=TimeInForce.FOK)
    )

    assert len(trades) == 2
    assert sum(t.quantity for t in trades) == 100


def test_market_order_crosses_regardless_of_price():
    book = OrderBook(instrument="PETR4")
    book.submit(make_order("sell1", Side.SELL, quantity=100, price=9999))

    trades = book.submit(
        make_order(
            "buy1", Side.BUY, quantity=100, price=None,
            order_type=OrderType.MARKET, time_in_force=TimeInForce.IOC,
        )
    )

    assert len(trades) == 1
    assert trades[0].price == 9999


def test_market_order_with_no_liquidity_produces_no_trades():
    book = OrderBook(instrument="PETR4")

    trades = book.submit(
        make_order(
            "buy1", Side.BUY, quantity=100, price=None,
            order_type=OrderType.MARKET, time_in_force=TimeInForce.IOC,
        )
    )

    assert trades == []


from matching_engine.engine.engine import MatchingEngine
from matching_engine.engine.messages import (
    CancelOrder,
    NewOrder,
    OrderAccepted,
    OrderCancelled,
    OrderExpired,
    OrderRejected,
    TradeExecuted
)
from matching_engine.order_book.order import OrderType, Side, TimeInForce

def new_order(
        order_id: str,
        side: Side,
        quantity: int,
        price: int | None = None,
        instrument: str = "PETR4",
        order_type: OrderType = OrderType.LIMIT,
        time_in_force: TimeInForce = TimeInForce.GTC,
    ) -> NewOrder:
        return NewOrder(
                instrument=instrument,
                order_id=order_id,
                client_order_id=f"c-{order_id}",
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                time_in_force=time_in_force,
        )

def test_order_that_does_not_cross_is_accepted_and_rests():
    engine = MatchingEngine()

    events = engine.handle(new_order("buy1", Side.BUY, quantity=100, price=3200))

    assert events == [OrderAccepted(instrument="PETR4", sequence=1, order_id="buy1")]

def test_crossing_orders_produce_a_trade():
      engine = MatchingEngine()

      engine.handle(new_order("sell1", Side.SELL, quantity=100, price=3250))

      events = engine.handle(new_order("buy1", Side.BUY, quantity=100, price=3250))

      assert len(events) == 2
      assert events[0] == OrderAccepted(instrument="PETR4", sequence=2, order_id="buy1")
      assert isinstance(events[1], TradeExecuted)
      assert events[1].sequence == 3
      assert events[1].trade.buy_order_id == "buy1"
      assert events[1].trade.sell_order_id == "sell1"
      assert events[1].trade.quantity == 100
      assert events[1].trade.price == 3250

def test_ioc_remainder_is_expired():
      engine = MatchingEngine()

      engine.handle(new_order("sell1", Side.SELL, quantity=30, price=3250))

      events = engine.handle(
            new_order("buy1", Side.BUY, quantity=100, price=3250, time_in_force=TimeInForce.IOC)
      )

      assert len(events) == 3
      assert isinstance(event[0], OrderAccepted)
      assert isinstance(event[1], TradeExecuted)
      assert events[1].trade.quantity == 30
      assert events[2] == OrderExpired(
            instrument="PETR4", sequence=4, order_id="buy1", remaing_quantity=70
      )

def test_fok_without_enough_quantity_is_accepted_then_expired_without_trades():
      engine = MatchingEngine()

      engine.handle(new_order("sell1", Side.SELL, quantity=30, price=3250))

      events = engine.handle(
            new_order("buy1", Side.BUY, quantity=100, price=3250, time_in_force=TimeInForce.FOK)
      )

      assert events == [
            OrderAccepted(instrument="PETR4", sequence=2, order_id="buy1"),
            OrderExpired(instrument="PETR4", sequence=3, order_id="buy1", remaing_quantity=100)
      ]



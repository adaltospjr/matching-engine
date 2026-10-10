
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

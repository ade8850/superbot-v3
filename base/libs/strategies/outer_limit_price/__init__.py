from typing import Tuple

from strategy_common.ioc import container
from strategy_common.models import Strategy

strategy: Strategy = container.strategy()


def set_outer_limit_price(price: float = None, reason: str = "shell"):
    subject = strategy.get_subject()
    if price is None:
        price = subject.get("price")
    subject.set("outer_limit_price_reason", reason, muted=True)
    subject.set("outer_limit_price", price)


def strategy_impl(price: float = None) -> Tuple[str, str | None]:
    this_ = "outer_limit_price"
    subject = strategy.get_subject()

    if price is None:
        price: float = subject.get("price")

    outer_limit_price: float = subject.get("outer_limit_price", default=None)

    if not outer_limit_price:
        return this_, None

    if price >= outer_limit_price:
        return this_, "Buy"
    return this_, "Sell"

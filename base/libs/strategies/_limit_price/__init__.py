from typing import Tuple

from strategy_common.ioc import container
from strategy_common.models import Strategy

strategy: Strategy = container.strategy()


def set_limit_price(price: float = None, reason: str = "shell"):
    subject = strategy.get_subject()
    if price is None:
        price = subject.get("price")
    subject.set("limit_price_reason", reason, muted=True)
    subject.set("limit_price", price)


def strategy_impl(price: float = None, **kwargs) -> Tuple[str, str | None]:
    this_ = "limit_price"
    subject = strategy.get_subject()

    if price is None:
        price: float = subject.get("price")

    limit_price: float = subject.get("limit_price", default=None)

    if not limit_price:
        return this_, None

    if price >= limit_price:
        return this_, "Buy"
    return this_, "Sell"

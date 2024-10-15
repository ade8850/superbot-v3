from typing import Tuple

from strategy_common.base_impl import StrategyImplBase


def strategy_impl(price: float, name: str, implementation: StrategyImplBase, **kwargs) -> Tuple[str, str | None]:
    this_ = name
    subject = implementation.strategy.get_subject()

    limit_price: float = subject.get(this_, default=None)

    if not limit_price:
        return this_, None

    if price >= limit_price:
        return this_, "Buy"
    return this_, "Sell"

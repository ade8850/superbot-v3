from typing import Tuple

from krules_core.subject.storaged_subject import Subject

from strategy_common.ioc import container
from strategy_common.models import Strategy

strategy: Strategy = container.strategy()


def strategy_impl(interval: str, period: int, price: float) \
        -> Tuple[str, str | None]:
    this_ = f"ema_{period}_{interval}"
    symbol: Subject = strategy.symbol.get_subject()

    property_ = f"ema_{period}_{interval}"
    value = symbol.get(property_, default=None)
    if value is None:
        return this_, None
    if price >= value:
        return this_, "Buy"
    else:
        return this_, "Sell"

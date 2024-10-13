from typing import Tuple

from krules_core.subject.storaged_subject import Subject

from strategy_common.ioc import container
from strategy_common.models import Strategy

strategy: Strategy = container.strategy()


def strategy_impl(interval: str, price: float, **kwargs) \
        -> Tuple[str, str | None]:

    _ = price  # unused in this strategy
    this_ = f"supertrend_dir_{interval}"

    symbol: Subject = strategy.symbol.get_subject()
    if symbol.get(this_, default=None) == 1:
        return this_, "Buy"
    elif symbol.get(this_, default=None) == -1:
        return this_, "Sell"
    else:
        return this_, None

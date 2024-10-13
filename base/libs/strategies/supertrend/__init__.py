import os
from typing import Tuple, List

from krules_core.subject.storaged_subject import Subject

from strategy_common.models import Strategy
from strategy_common.utils import calculate_pnl

from strategy_common.ioc import container

strategy: Strategy = container.strategy()


def set_limit_price_to_supertrend(price: float, entry_price: float, intervals: List[str], subject: Subject,
                                  symbol: Subject) \
        -> Tuple[str, float, float] | None:
    action = subject.get("action", default=None)
    if action not in ["Buy", "Sell"]:
        return None

    found: Tuple[str, float, float] | None = None

    margin = subject.get("margin", default=100)

    _fee = 0
    if bool(eval(os.environ.get("SET_LIMIT_TO_SUPERTREND_INCLUDE_FEE", "1"))):
        _fee = strategy.fee

    for property, property_dir in [(f"supertrend_{interval}", f"supertrend_dir_{interval}") for interval in intervals]:
        st_price = symbol.get(property, default=None)
        st_dir = symbol.get(property_dir, default=None)

        if st_price is not None:
            if (action == "Buy" and st_dir == 1 and st_price > entry_price
                    or action == "Sell" and st_dir == -1 and st_price < entry_price):
                if action == "Buy" and price < st_price or action == "Sell" and price > st_price:
                    continue
                pl = calculate_pnl(margin, action, strategy.leverage, _fee, entry_price, st_price)
                if pl > 0:
                    found = property, st_price, pl
                else:
                    break

    if found is not None:
        subject.set("limit_price_reason", found[0], muted=True)
        subject.set("limit_price", found[1])

    return found


def strategy_impl(interval: str, price: float, **kwargs) \
        -> Tuple[str, str | None]:
    this_ = f"supertrend_{interval}"

    limit = strategy.symbol.get_subject().get(this_, default=None)
    if limit is None:
        return this_, None

    if price > limit:
        return this_, "Buy"
    else:
        return this_, "Sell"



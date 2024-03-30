from typing import Tuple

from krules_core.subject.storaged_subject import Subject

from strategies.strategy import get_subject, get_symbol


def strategy(interval: str, period: int, price: float, symbol: Subject = None) \
        -> Tuple[str, str | None]:
    this_ = f"ema_{period}_{interval}"
    if symbol is None:
        symbol = get_symbol().get_subject()

    property_ = f"ema_{interval}"
    value = symbol.get(property_, default={}).get(str(period))
    if value is None:
        return this_, None
    if price >= value:
        return this_, "Buy"
    else:
        return this_, "Sell"

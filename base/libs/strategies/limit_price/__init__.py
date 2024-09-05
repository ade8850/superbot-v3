from typing import Tuple

from krules_core.subject.storaged_subject import Subject

#from strategies.strategy import get_subject


def set_limit_price(price: float = None, reason: str = "shell", subject: Subject = None):
#    if subject is None:
#        subject = get_subject()
    if price is None:
        price = subject.get("price")
    subject.set("limit_price_reason", reason, muted=True)
    subject.set("limit_price", price)


def strategy(price: float = None, subject: Subject = None) -> Tuple[str, str | None]:
    this_ = "limit_price"
#    if subject is None:
#        subject = get_subject()
    if price is None:
        price: float = subject.get("price")

    limit_price: float = subject.get("limit_price", default=None)

    if not limit_price:
        return this_, None

    if price >= limit_price:
        return this_, "Buy"
    return this_, "Sell"

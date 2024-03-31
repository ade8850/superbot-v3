from krules_core.subject.storaged_subject import Subject

from app_common.utils import calculate_pnl
from strategies.common import get_verb_from
from strategies.common.action import set_action
from strategies.common.verb import is_opposite
from strategies.limit_price import strategy as limit_price_strategy
from strategies.strategy import get_symbol, leverage, fee
from strategies.supertrend import (
    strategy as supertrend_strategy,
    dir_strategy as supertrend_dir_strategy,
    set_limit_price_to_supertrend,
)

symbol = get_symbol().get_subject(use_cache_default=False)


def perform(price: float, subject: Subject) -> dict:
    _limit_price_strategy = limit_price_strategy(price, subject)
    _supertrend_T = supertrend_strategy("T", price, symbol)
    #_supertrend_dir_T = supertrend_dir_strategy("T", price, symbol)
    #_supertrend_3T = supertrend_strategy("3T", price, symbol)
    #_supertrend_dir_3T = supertrend_dir_strategy("3T", price, symbol)
    # _supertrend_5T = supertrend_strategy("5T", price, symbol)
    # _supertrend_15T = supertrend_strategy("15T", price, symbol)
    # _supertrend_30T = supertrend_strategy("30T", price, symbol)
    # _supertrend_H = supertrend_strategy("H", price, symbol)
    # _supertrend_2H = supertrend_strategy("2H", price, symbol)
    # _supertrend_4H = supertrend_strategy("4H", price, symbol)
    # # _ema_100_T = ema_strategy("T", 100, price, symbol)

    return_ = {}

    new_limit_found = None
    if (action := subject.get("action", default=None)) in ("Buy", "Sell"):
        action_entry_price = subject.get("action_entry_price", default=None)
        if action_entry_price is not None:
            margin = subject.get("margin", default=100)
            pnl = calculate_pnl(margin, action, leverage, fee, action_entry_price, price)
            return_["pnl"] = (pnl, pnl/margin*100)
            new_limit_found = set_limit_price_to_supertrend(
                price, action_entry_price,
                ["3T", "5T", "15T"],
                subject, symbol
            )
            return_["new_limit"] = new_limit_found

        _, limit = _limit_price_strategy
        # _, ema_100_T = _ema_100_T
        _, st1 = _supertrend_T
        #_, st3 = _supertrend_3T

        _neg = lambda strategy: is_opposite(action, strategy)

        if _neg(limit) and _neg(st1):
            #reason = new_limit_found is None and "loss" or "profit"
            # symbol.set("supertrend_dir_T", None, muted=True, use_cache=False)
            set_action("stop", reason="strategy", subject=subject)

    open_strategies = [
        _limit_price_strategy,
        _supertrend_T,
        #_supertrend_dir_T,
        #_supertrend_3T,
        #_supertrend_dir_3T,
    ]

    subject.verb, op_strat_results = get_verb_from(open_strategies,
                                                   _for=price, subject=subject)

    return_["verbs"] = op_strat_results

    return return_

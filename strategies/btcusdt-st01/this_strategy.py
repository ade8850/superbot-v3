import rich
from krules_core.subject.storaged_subject import Subject

from strategies.ema import strategy_impl as ema_strategy
from strategies.outer_limit_price import strategy_impl as outer_limit_price_strategy
from strategies.supertrend import (
    strategy_impl as supertrend_strategy,
)
from strategies.supertrend_dir import strategy_impl as supertrend_dir_strategy
from strategy_common.action import set_action
from strategy_common.ioc import container
from strategy_common.models import Strategy
from strategy_common.verb import get_verb_from, is_opposite

strategy: Strategy = container.strategy()

def perform(price: float) -> dict:
    subject: Subject = strategy.get_subject()

    #    _limit_price_strategy = limit_price_strategy(price)
    _outer_limit_price_strategy = outer_limit_price_strategy(price)
    _supertrend_T = supertrend_strategy("T", price)
    _supertrend_dir_T = supertrend_dir_strategy("T", price)
    _supertrend_3T = supertrend_strategy("3T", price)
    _supertrend_dir_3T = supertrend_dir_strategy("3T", price)
    _ema_100_4h = ema_strategy("4H", 100, price)
    _ema_100_h = ema_strategy("H", 100, price)
    _ema_100_T = ema_strategy("T", 100, price)

    return_ = {}

    new_limit_found = None
    if (action := subject.get("action", default=None)) in ("Buy", "Sell"):
        # action_entry_price = subject.get("action_entry_price", default=None)
        # if action_entry_price is not None:
        #     margin = subject.get("margin", default=100)
        #     pnl = calculate_pnl()
        #     return_["pnl"] = (pnl, pnl / margin * 100)
        #     new_limit_found = set_limit_price_to_supertrend(
        #         price, action_entry_price,
        #         ["3T", "5T", "15T"],
        #         subject, strategy.symbol.get_subject()
        #     )
        #     return_["new_limit"] = new_limit_found

        _, outer_limit = _outer_limit_price_strategy
        _, ema_100_4h = _ema_100_4h
        _, ema_100_h = _ema_100_h
        _, ema_100_T = _ema_100_T
        _, st1 = _supertrend_T
        #_, st1 = _supertrend_T
        #_, st3 = _supertrend_3T

        _neg = lambda strategy: is_opposite(action, strategy)

        if (_neg(outer_limit) or _neg(ema_100_h)) and _neg(st1) and _neg(ema_100_T):  # and _neg(st3):
            #rich.print(f"?? ({_neg(outer_limit)} or {_neg(ema_100_4h)}) and {_neg(ema_100_T)}")
            #reason = new_limit_found is None and "loss" or "profit"
            # symbol.set("supertrend_dir_T", None, muted=True, use_cache=False)
            set_action("stop", reason="strategy")
        # else:
        #     rich.print(f"?? ({_neg(outer_limit)} or {_neg(ema_100_4h)}) and {_neg(st1)}")

    open_strategies = [
        #        _limit_price_strategy,
        _outer_limit_price_strategy,
        _ema_100_h,
        _ema_100_T,
        _supertrend_T,
        _supertrend_dir_T,
        #_supertrend_3T,
        #_supertrend_dir_3T,
        # _supertrend_5T,
        # _supertrend_15T,
    ]

    subject.verb, op_strat_results = get_verb_from(open_strategies,
                                                   _for=price, subject=subject)

    return_["verbs"] = op_strat_results

    return return_

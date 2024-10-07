import rich
from krules_core.subject.storaged_subject import Subject

from celery_app.tasks import cm_publish
from strategy_common.models import Strategy
from strategy_common.utils import calculate_pnl
from strategy_common.verb import get_verb_from, is_opposite
from strategy_common.action import set_action
from strategies.limit_price import strategy_impl as limit_price_strategy
from strategies.outer_limit_price import strategy_impl as outer_limit_price_strategy
from strategies.supertrend import (
    strategy_impl as supertrend_strategy,
    dir_strategy_impl as supertrend_dir_strategy,
    set_limit_price_to_supertrend,
)
from strategies.ema import strategy_impl as ema_strategy

from strategy_common.ioc import container

strategy: Strategy = container.strategy()


def on_minute():
    rich.print("@@@@@@@@@@@@@@@@@@@ ON MINUTE @@@@@@@@@@@@@@@@@@@")
    estimated_pnl = None
    try:
        subject = strategy.get_subject()
        action = subject.get("action", default=None)
        if action in ("Buy", "Sell"):
            rich.print(">> calculate  pnl")
            outer_limit_price = subject.get("outer_limit_price")
            ref_indicator_price = strategy.symbol.get_subject().get(strategy.outerLimitFollows)
            ref_price = None
            if strategy.outerLimitFollows is not None:
                if action == "Buy":
                    ref_price = max(outer_limit_price, ref_indicator_price)
                else:
                    ref_price = min(outer_limit_price, ref_indicator_price)
                rich.print(f">> ref_price: {ref_price}")
            estimated_pnl = calculate_pnl(price=ref_price, side=action)
            rich.print(f">> estimated_pnl: {estimated_pnl}")
    except Exception as ex:
        rich.print("!!!!!!!!!!! ERROR !!!!!!!!!!!")
        rich.print(ex)

    strategy.publish(
        estimated_pnl=estimated_pnl
    )


def perform(price: float) -> dict:
    subject: Subject = strategy.get_subject()

    #    _limit_price_strategy = limit_price_strategy(price)
    _outer_limit_price_strategy = outer_limit_price_strategy(price)
    _supertrend_T = supertrend_strategy("T", price)
    _supertrend_dir_T = supertrend_dir_strategy("T", price)
    _supertrend_3T = supertrend_strategy("3T", price)
    _supertrend_dir_3T = supertrend_dir_strategy("3T", price)
    _ema_100_4h = ema_strategy("4H", 100, price)

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
        _, st1 = _supertrend_T
        _, st3 = _supertrend_3T

        _neg = lambda strategy: is_opposite(action, strategy)

        if (_neg(outer_limit) or _neg(ema_100_4h)) and _neg(st1) and _neg(st3):
            #reason = new_limit_found is None and "loss" or "profit"
            # symbol.set("supertrend_dir_T", None, muted=True, use_cache=False)
            set_action("stop", reason="strategy")

    open_strategies = [
        #        _limit_price_strategy,
        _outer_limit_price_strategy,
        _ema_100_4h,
        _supertrend_T,
        _supertrend_dir_T,
        _supertrend_3T,
        #_supertrend_dir_3T,
        # _supertrend_5T,
        # _supertrend_15T,
    ]

    subject.verb, op_strat_results = get_verb_from(open_strategies,
                                                   _for=price, subject=subject)

    return_["verbs"] = op_strat_results

    return return_

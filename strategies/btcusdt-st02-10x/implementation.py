from functools import partial

from rich.console import Console

from strategy_common import is_opposite
from strategy_common.base_impl import StrategyImplBase

console = Console()


class StrategyImpl(StrategyImplBase):

    def check_close(self, action: str) -> bool:
        assert action in ("Buy", "Sell")
        bounds = self.values["bound"].values()
        closes = self.values["close"].values()
        neg = partial(is_opposite, action)
        if any(map(neg, bounds)) and all(closes):
            return True
        return False

    def get_pnl_ref_price(self, side) -> float:
        subject = self.strategy.get_subject()
        outer_limit_price = subject.get("outer_limit_price")
        ref_indicator_price = self.strategy.symbol.get_subject().get("ema_100_4H")  # TODO
        #if self.strategy.outerLimitFollows is not None:
        if side == "Buy":
            return max(outer_limit_price, ref_indicator_price)
        else:
            return min(outer_limit_price, ref_indicator_price)

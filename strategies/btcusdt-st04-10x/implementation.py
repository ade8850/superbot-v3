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

    def get_pnl_ref_price(self, side) -> float | None:
        subject = self.strategy.get_subject()
        bounds = list(filter(lambda x: x is not None, [subject.get(key, default=None) for key in self.values["bound"]]))
        if not len(bounds):
            return None
        if side == "Buy":
            return max(bounds)
        else:
            return min(bounds)

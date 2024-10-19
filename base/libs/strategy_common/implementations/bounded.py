from functools import partial
from typing import Tuple, Optional

from rich.console import Console

from strategy_common import is_opposite
from strategy_common.base_impl import StrategyImplBase

console = Console()


class BoundedStrategyImpl(StrategyImplBase):

    def check_close(self, action: str) -> bool:
        console.print("> Checking close", style="bold")
        assert action in ("Buy", "Sell")

        # Get the bound indicators
        bounds = list(self.values["bound"].values())
        console.print(f"> Bounds: {bounds}", style="dim")

        # Get the close indicators
        closes = list(self.values["close"].values())
        console.print(f"> Closes: {closes}", style="dim")

        # Check if at least one bound is opposite to the current action
        neg = partial(is_opposite, action)
        any_opposite_bound = any(map(neg, bounds))
        console.print(f"> Any opposite bound: {any_opposite_bound}", style="dim")

        # Check if all closes are opposite to the current action
        all_opposite_closes = all(map(neg, closes))
        console.print(f"> All opposite closes: {all_opposite_closes}", style="dim")

        # Return True if at least one bound is opposite AND all closes are opposite
        should_close = any_opposite_bound and all_opposite_closes
        console.print(f"> Should close: {should_close}", style="green" if should_close else "red")

        return should_close


    # def get_pnl_ref_price(self, side) -> float | None:
    #     subject = self.strategy.get_subject()
    #     bounds = list(filter(lambda x: x is not None, [subject.get(key, default=None) for key in self.values["bound"]]))
    #     closes = list(filter(lambda x: x is not None, [subject.get(key, default=None) for key in self.values["close"]]))
    #
    #     if not bounds and not closes:
    #         return None
    #
    #     if side == "Buy":
    #         if not closes:
    #             return max(bounds) if bounds else None
    #         elif not bounds:
    #             return min(closes)
    #         else:
    #             return max(max(bounds), min(closes))
    #     else:  # side == "Sell"
    #         if not closes:
    #             return min(bounds) if bounds else None
    #         elif not bounds:
    #             return max(closes)
    #         else:
    #             return min(min(bounds), max(closes))

    def get_pnl_ref_price(self, side: str) -> Tuple[Optional[float], Optional[str]]:
        strategy_subject = self.strategy.get_subject()
        symbol_subject = self.strategy.symbol.get_subject()

        bounds = {}
        closes = {}

        console.print(f"Processing bounds and closes: {self.values['bound']} {self.values['close']}", style="dim")

        # Processiamo i bounds dal strategy_subject
        for key in self.values['bound']:
            try:
                bound_value = strategy_subject.get(key, default=None)
                if bound_value is not None:
                    bounds[key] = float(bound_value)
            except (AttributeError, ValueError) as e:
                console.print(f"Error processing bound {key}: {e}", style="yellow")

        # Processiamo i closes dal symbol_subject
        for key in self.values['close']:
            try:
                close_value = symbol_subject.get(key, default=None)
                if close_value is not None:
                    closes[key] = float(close_value)
            except (AttributeError, ValueError) as e:
                console.print(f"Error processing close {key}: {e}", style="yellow")

        console.print(f"Processed bounds: {bounds}", style="dim")
        console.print(f"Processed closes: {closes}", style="dim")

        if not bounds and not closes:
            console.print("No valid bounds or closes found", style="bold red")
            return None, None

        if side == "Buy":
            if bounds:
                max_bound = max(bounds.items(), key=lambda x: x[1])
                if closes:
                    min_close = min(closes.items(), key=lambda x: x[1])
                    if min_close[1] <= max_bound[1]:
                        console.print(f"Buy: Using close {min_close}", style="green")
                        return min_close[1], min_close[0]
                console.print(f"Buy: Using bound {max_bound}", style="green")
                return max_bound[1], max_bound[0]
            elif closes:
                min_close = min(closes.items(), key=lambda x: x[1])
                console.print(f"Buy: Using close {min_close}", style="green")
                return min_close[1], min_close[0]

        else:  # side == "Sell"
            if bounds:
                min_bound = min(bounds.items(), key=lambda x: x[1])
                if closes:
                    max_close = max(closes.items(), key=lambda x: x[1])
                    if max_close[1] >= min_bound[1]:
                        console.print(f"Sell: Using close {max_close}", style="green")
                        return max_close[1], max_close[0]
                console.print(f"Sell: Using bound {min_bound}", style="green")
                return min_bound[1], min_bound[0]
            elif closes:
                max_close = max(closes.items(), key=lambda x: x[1])
                console.print(f"Sell: Using close {max_close}", style="green")
                return max_close[1], max_close[0]

        console.print("Unable to determine reference price", style="bold red")
        return None, None
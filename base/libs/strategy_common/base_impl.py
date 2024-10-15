import abc
import importlib
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from strategy_common.models import Strategy, SessionConfig

from rich.console import Console
from rich.traceback import Traceback

console = Console()


class StrategyImplBase(ABC):

    @abstractmethod
    def check_close(self, action: str) -> bool:
        """
        Check if is time to close the position
        This is ment to be called only during an action.

        Args:
            action: Current action (Buy or Sell)
        Returns:
            True if the position should be closed, False otherwise
        """

    @abstractmethod
    def get_pnl_ref_price(self, side) -> float | None:
        """
        Return the reference price to calculate the PnL. It is called only during an action.
        Args:
            side: current action (Buy or Sell)

        Returns:
            the price to calculate the PnL
        """

    def __init__(self, strategy: Strategy):
        console.rule("STARTUP")
        self._strategy = strategy
        self._values: Dict[str, Dict[str, str]] = {}

    @property
    def values(self) -> Dict[str, Dict[str, str]]:
        return self._values

    def reset_session(self):
        self._values: Dict[str, Dict[str, str]] = {'__all__': {}}

    def session(self, price):
        self.reset_session()
        session_config: SessionConfig = self.strategy.session
        for strategy_config in session_config.strategies:
            strategy_name = strategy_config.strategy

            try:
                self.set_value(
                    strategy_name,
                    strategy_config.groups,
                    **strategy_config.kwargs,
                    price=price,
                    implementation=self,
                )
            except Exception as ex:
                console.log(f"!!!!!!!!!!! {strategy_name} > ERROR !!!!!!!!!!!")
                tb = Traceback.from_exception(type(ex), ex, ex.__traceback__)
                console.print(tb)

    def set_value(self, strategy_name: str, groups: List[str], *args, **kwargs):
        try:
            # Dynamically import the module
            module = importlib.import_module(f"strategies.{strategy_name}")
            # Get the function
            strategy_func = getattr(module, "strategy_impl")
            # Call the function
            _name, value = strategy_func(*args, **kwargs)

            for group in groups:
                if group not in self._values:
                    self._values[group] = {}
                self._values[group][_name] = value
            self._values["__all__"][_name] = value

        except ImportError:
            console.log(f"Error: Could not import module 'strategies.{strategy_name}'", style="bold red")
        except AttributeError:
            console.log(f"Error: Module 'strategies.{strategy_name}' does not have a function named 'strategy_impl'",
                        style="bold red")

    def get_common_verb(self) -> str | None:
        if filtered_strategies := [strat for strat in self.values["__all__"] if
                                   self.values["__all__"][strat] is not None]:
            reference_verb = self.values["__all__"][filtered_strategies[0]]
            for strat in filtered_strategies[1:]:
                if self.values["__all__"][strat] != reference_verb:
                    return None

            return reference_verb
        return None

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    def on_minute(self):
        from strategy_common.utils import calculate_pnl

        console.rule("ON MINUTE")

        estimated_pnl = None
        try:
            subject = self.strategy.get_subject()
            action = subject.get("action", default=None)
            if action in ("Buy", "Sell"):
                ref_price = self.get_pnl_ref_price(side=action)
                if ref_price:
                    estimated_pnl = calculate_pnl(price=ref_price, side=action)
                    console.print(f"Got new estimated PnL: {estimated_pnl}")
                else:
                    console.print("Cannot estimate PnL")
        except Exception as ex:
            console.log("!!!!!!!!!!! ON MINUTE > ERROR !!!!!!!!!!!")
            tb = Traceback.from_exception(type(ex), ex, ex.__traceback__)
            console.print(tb)

        self.strategy.publish(
            estimated_pnl=estimated_pnl
        )

    def on_indicator(self, indicator, value, old_value):
        console.rule(f"ON INDICATOR {indicator}")
        subject = self.strategy.get_subject()

        for limit in self.strategy.limits:

            if not limit.follows == indicator:
                continue

            limit_price = subject.get(limit.name, default=None)

            if not limit_price:
                continue

            console.print(f">> MATCHES {limit.name}")
            console.print(f">> {value}, {old_value}")

            cur_price = subject.get("price")

            diff = value - old_value

            new_limit_price = limit_price + diff
            changed = False
            if cur_price > limit_price:
                if diff > 0:
                    console.print(f"[green]++ increase {limit.name} to {new_limit_price}[/green]")
                    subject.set(limit.name, new_limit_price)
                    changed = True
            elif cur_price < limit_price:
                if diff < 0:
                    console.print(f"[red]-- decrease {limit.name} to {new_limit_price}[/red]")
                    subject.set(limit.name, new_limit_price)
                    changed = True

            if not changed:
                console.print(f"[grey85]== {limit.name} is stable[/grey85]")
            else:
                self.strategy.publish(**{limit.name: new_limit_price})


    def on_action(self, action, price):
        console.rule(f"ON ACTION {action}")

        subject = self.strategy.get_subject()
        subject.set("action_entry_price", price, muted=True, use_cache=False)
        subject.set("side", action, use_cache=False)

        for limit in self.strategy.limits:

            if limit.reset_on_action == "if_none":
                if subject.get(limit.name, default=None) is None:
                    subject.set(limit.name, price, muted=True, use_cache=False)
                    self.strategy.publish(**{limit.name: price})
                continue

            if limit.reset_on_action == "always":
                subject.set(limit.name, price, muted=True, use_cache=False)
                self.strategy.publish(**{limit.name: price})
                continue



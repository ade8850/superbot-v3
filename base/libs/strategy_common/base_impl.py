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
    def get_pnl_ref_price(self, side) -> float:
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

    def set_value(self, name: str, groups: List[str], *args, **kwargs):
        try:
            # Dynamically import the module
            module = importlib.import_module(f"strategies.{name}")
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
            console.log(f"Error: Could not import module 'strategies.{name}'", style="bold red")
        except AttributeError:
            console.log(f"Error: Module 'strategies.{name}' does not have a function named 'strategy_impl'",
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
                estimated_pnl = calculate_pnl(price=ref_price, side=action)
                console.print(f"Got new estimated PnL: {estimated_pnl}")
        except Exception as ex:
            console.log("!!!!!!!!!!! ON MINUTE > ERROR !!!!!!!!!!!")
            tb = Traceback.from_exception(type(ex), ex, ex.__traceback__)
            console.print(tb)

        self.strategy.publish(
            estimated_pnl=estimated_pnl
        )

import time

from krules_core.base_functions.processing import ProcessingFunction

from strategy_common.utils import calculate_pnl

from strategy_common.ioc import container
strategy = container.strategy()
leverage = strategy.leverage
fee = strategy.fee


class UpdateMargin(ProcessingFunction):

    def execute(self, from_action: str, sleep: int):

        subject = strategy.get_subject()

        margin = subject.get("margin", default=100)

        pl = calculate_pnl(margin=margin, side=from_action)

        subject.set("margin", margin+pl)
        subject.store()

        time.sleep(sleep)
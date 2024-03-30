import time

from krules_core.base_functions.processing import ProcessingFunction

from app_common.utils import calculate_pnl
from strategies.strategy import leverage, fee


class UpdateMargin(ProcessingFunction):

    def execute(self, from_action: str, sleep: int):

        subject = self.subject
        margin = subject.get("margin", default=100)
        entry_price = subject.get("action_entry_price")
        price = subject.get("price")

        pl = calculate_pnl(margin, from_action, leverage, fee, entry_price, price)

        subject.set("margin", margin+pl)
        subject.store()

        time.sleep(sleep)
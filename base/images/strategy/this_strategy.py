from krules_core.subject.storaged_subject import Subject
from strategies.models import StrategySettings

config = StrategySettings()


def perform(price: float, subject: Subject) -> dict:
    return {}

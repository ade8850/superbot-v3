import os

from krules_core.providers import subject_factory
from krules_core.subject.storaged_subject import Subject

from app_common.models import Symbol
from celery_app.tasks import cm_publish

name = os.environ['APP_NAME'].replace("strategy-", "", 1).lower()
symbol = os.environ.get('SYMBOL').lower()
provider = os.environ.get('PROVIDER', "bybit").lower()
category = os.environ.get('CATEGORY', "linear").lower()

leverage = int(os.environ.get("LEVERAGE", "1"))
fee = float(os.environ.get("TAKER_FEE", "0.00055"))



def get_subject() -> Subject:
    return subject_factory(f"strategy|{provider}|{name}", use_cache_default=False)


def get_symbol() -> Symbol:
    return Symbol(
        name=symbol,
        category=category,
        provider=provider,
    )


def publish(**kwargs):
    cm_publish.delay(
        group=f"strategies.{provider}",
        entity=name,
        properties=kwargs
    )

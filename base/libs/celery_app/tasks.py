import os

import celery

from app_common.models import Symbol
from . import app

try:
    import krules_env

    krules_env.init()
except:  # avoid circular import
    pass

from krules_core.providers import event_router_factory


all_symbols = os.environ.get("ALL_SYMBOLS", "").split(",")


class BaseTask(celery.Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        event_router_factory().route(
            "sys.celery.worker.failed",
            f"tasks|{task_id}",
            {
                "exc": exc,
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "einfo": einfo,
            },
            topic=os.environ["SCHEDULER_ERRORS_TOPIC"]
        )


@app.task(base=BaseTask, bind=True, ignore_result=True)
def bybit_process_kline_data(*args, **kwargs):
    from bybit.tasks import process_kline_data
    return process_kline_data(*args, **kwargs)


@app.task(base=BaseTask, bind=True, ignore_result=True)
def bybit_update_instrument_info(*args, **kwargs):
    from bybit.tasks import update_instrument_info
    for symbol in all_symbols:
        update_instrument_info(symbol=Symbol(
            name=symbol,
            category="linear",
            provider="bybit"
        ))
    return {}

@app.task(base=BaseTask, bind=True, ignore_result=True)
def companion_check_strategies(*args, **kwargs):
    from krules_companion_client.http import HttpClient
    client = HttpClient()
    client.callback("strategies.bybit", channels=["callbacks"],  message="check_strategies")


@app.task(base=BaseTask, bind=False, ignore_result=True)
def cm_publish(**kwargs):
    from krules_companion_client.http import HttpClient
    client = HttpClient()
    client.publish(**kwargs)

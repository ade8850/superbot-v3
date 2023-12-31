import os

import celery

from . import app

try:
    import krules_env

    krules_env.init()
except:  # avoid circular import
    pass

from krules_core.providers import event_router_factory


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

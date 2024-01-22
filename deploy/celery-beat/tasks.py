from celery_app.tasks import *


@app.on_after_configure.connect
def add_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(600, bybit_update_instrument_info, name='bybit update instrument info')

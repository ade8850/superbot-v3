import os

from celery import Celery
from google.cloud import secretmanager

app_kwargs = {}

client = secretmanager.SecretManagerServiceClient()
celery_broker = os.environ.get("CELERY_BROKER")
if celery_broker is None:
    secret_path = os.environ.get("CELERY_BROKER_SECRET_PATH")
    if secret_path:
        response = client.access_secret_version(name=secret_path)
        celery_broker = response.payload.data.decode('utf-8')
celery_result_backend = os.environ.get("CELERY_RESULT_BACKEND")
if celery_result_backend is None:
    secret_path = os.environ.get("CELERY_RESULT_BACKEND_SECRET_PATH")
    if secret_path:
        response = client.access_secret_version(name=secret_path)
        celery_result_backend = response.payload.data.decode('utf-8')

if celery_broker is not None:
    app_kwargs["broker"] = celery_broker
if celery_result_backend is not None:
    app_kwargs["result_backend"] = celery_result_backend

app = Celery(
    'sb-scheduler',
    **app_kwargs
)


class CeleryConfig:
    task_serializer = "pickle"
    result_serializer = "pickle"
    event_serializer = "json"
    accept_content = ["application/json", "application/x-python-serialize"]
    result_accept_content = ["application/json", "application/x-python-serialize"]
    task_store_errors_even_if_ignored = True


app.config_from_object(CeleryConfig)

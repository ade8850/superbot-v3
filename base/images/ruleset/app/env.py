import logging
import os

import google.auth
from dependency_injector import providers
from krules_cloudevents_pubsub.route.dispatcher import CloudEventsDispatcher
from krules_core.providers import event_dispatcher_factory, subject_storage_factory
from krules_env import get_source, RULE_PROC_EVENT
from redis_subjects_storage.storage_impl import SubjectsRedisStorage

logger = logging.getLogger()

_, PROJECT = google.auth.default()

cache_secrets = {}


def _get_topic_id(subject, event_type):
    # TODO: remove me
    from krules_core.providers import subject_factory, event_router_factory
    print(f"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ _get_topic_id> {str(subject)}, {str(event_type)}")
    subject = subject_factory(subject)
    print(f">>>> subject storage: {subject._storage}")
    print(f">>>> rules: {str(event_router_factory()._callables)}")
    # END TODO
    if event_type == RULE_PROC_EVENT:
        print(">>>>> GOT PROC EVENT")
        return os.environ.get("PROCEVENTS_TOPIC", os.environ.get("DEFAULTSINK_TOPIC"))
    else:
        topic_name = os.environ.get("DEFAULTSINK_TOPIC")

    return topic_name


def get_secret(secret_name: str, default=None) -> str:
    from google.cloud import secretmanager

    global cache_secrets
    secret_name = secret_name.upper()
    if secret_name in os.environ:
        return os.environ[secret_name]
    if secret_name in cache_secrets:
        return cache_secrets[secret_name]
    secret_path = os.environ.get(f"{secret_name}_SECRET_PATH")
    if secret_path:
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_path)
        cache_secrets[secret_name] = response.payload.data.decode('utf-8')
        return cache_secrets[secret_name]
    return default


def init():

    event_dispatcher_factory.override(
        providers.Singleton(lambda: CloudEventsDispatcher(
            project_id=PROJECT,
            topic_id=_get_topic_id,
            source=get_source(),
        ))
    )

    subjects_redis_url = get_secret("SUBJECTS_REDIS_URL")
    if subjects_redis_url:
        subjects_redis_prefix = os.environ.get("SUBJECTS_REDIS_PREFIX")
        if subjects_redis_prefix is None:
            if "PROJECT_NAME" in os.environ and "TARGET" in os.environ:
                subjects_redis_prefix = f"{os.environ['PROJECT_NAME']}-{os.environ['TARGET']}->"
            else:
                raise Exception("SUBJECTS_REDIS_PREFIX not configured")
        subject_storage_factory.override(
            providers.Factory(
                lambda name, **kwargs:
                SubjectsRedisStorage(
                    name,
                    subjects_redis_url,
                    key_prefix=subjects_redis_prefix
                )
            )
        )

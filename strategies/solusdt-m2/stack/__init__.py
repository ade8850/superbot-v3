import pulumi
from pulumi import Config
from pulumi_gcp.artifactregistry import Repository
from pulumi_gcp.pubsub import Topic
from pulumi_gcp.firestore import Database
from pulumi_kubernetes.core.v1 import EnvVarArgs

from krules_dev import sane_utils
from krules_dev.sane_utils import get_stack_reference
from krules_dev.sane_utils.pulumi.components import GkeDeployment

config = Config()

app_name = sane_utils.check_env("app_name")

base_stack_ref = get_stack_reference("base")

gcp_repository = Repository.get(
    "gcp_repository",
    base_stack_ref.require_output("docker-repository.id")
)

topic_signals = Topic.get(
    "signals",
    base_stack_ref.require_output("topics.signals.id")
)

deployment = GkeDeployment(
    app_name,
    gcp_repository=gcp_repository,
    access_secrets=[
        "subjects_redis_url",
        "celery_broker",
    ],
    publish_to={
        # "my-topic": my_topic,
    },
    subscriptions_inject_sidecar=False,
    subscribe_to=[
        # (
        #     "ema_100_4H", {
        #         "topic": topic_signals.name,
        #         "project": topic_signals.project,
        #         "ack_deadline_seconds": 20,
        #         "filter": 'attributes.subject="signal:bybit:perpetual:btcusdt:ema_100_4H"'
        #     },
        # ),
        (
            "ema_100", {
                "topic": topic_signals.name,
                "project": topic_signals.project,
                "ack_deadline_seconds": 20,
                "message_retention_duration": "600s",
                "filter": 'hasPrefix(attributes.subject, "signal:bybit:perpetual:solusdt:ema_100_")'
            },
        ),
    ],
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="SET_LIMIT_TO_SUPERTREND_INCLUDE_FEE",
                value="1"
            ),
        ]
    }
)


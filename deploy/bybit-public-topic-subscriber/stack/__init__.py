import pulumi
from pulumi import Config
from pulumi_gcp.artifactregistry import Repository
from pulumi_gcp.pubsub import Topic
from pulumi_kubernetes.core.v1 import EnvVarArgs

from krules_dev import sane_utils
from krules_dev.sane_utils import get_stack_reference
from krules_dev.sane_utils.pulumi.components import GkeDeployment

config = Config()

app_name = sane_utils.check_env("app_name")

base_stack_ref = get_stack_reference("base")

gcp_repository = Repository.get(
    "gcp_repository",
    base_stack_ref.get_output(
        "docker-repository"
    ).apply(
        lambda repository: repository.get("id")
    )
)

topic_bybit_public = Topic.get(
    "bybit-public",
    base_stack_ref.get_output(
        "topics"
    ).apply(
        lambda topics: topics.get("bybit-public").get("id")
    )
)

deployment = GkeDeployment(
    app_name,
    gcp_repository=gcp_repository,
    access_secrets=[
    ],
    subscribe_to=[
        (
            "bybit-public",
            {
                "topic": topic_bybit_public.name,
                "message_retention_duration": "600s",
                "ack_deadline_seconds": 20,
            }
        ),
    ],
)


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
    publish_to={
        "bybit_public": topic_bybit_public,
    },
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="SUBSCRIBE_SYMBOLS",
                value=sane_utils.get_var_for_target("subscribe_symbols")
            ),
            EnvVarArgs(
                name="SUBSCRIBE_KLINE",
                value=sane_utils.get_var_for_target("subscribe_kline")
            ),
            EnvVarArgs(
                name="SUBSCRIBE_TICKER",
                value=sane_utils.get_var_for_target("subscribe_ticker")
            ),
        ]
    }
)


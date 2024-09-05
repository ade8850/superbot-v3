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

# gcp_repository = Repository.get(
#     "gcp_repository",
#     base_stack_ref.get_output(
#         "docker-repository"
#     ).apply(
#         lambda repository: repository.get("id")
#     )
# )

gcp_repository = Repository.get(
    "gcp_repository",
    base_stack_ref.require_output("docker-repository.id")
)

topic_procevents = Topic.get(
    "procevents",
    base_stack_ref.require_output("topics.procevents.id")
)

# topic_procevents = Topic.get(
#     "procevents",
#     base_stack_ref.get_output(
#         "topics"
#     ).apply(
#         lambda topics: topics.get("procevents").get("id")
#     )
# )


# topic_bybit_public = Topic.get(
#     "bybit-public",
#     base_stack_ref.get_output(
#         "topics"
#     ).apply(
#         lambda topics: topics.get("bybit-public").get("id")
#     )
# )

deployment = GkeDeployment(
    app_name,
    gcp_repository=gcp_repository,
    access_secrets=[
        "subjects_redis_url",
        "celery_broker",
    ],
    publish_to={
        "procevents": topic_procevents,
    },
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="ALL_SYMBOLS",
                value=sane_utils.get_var_for_target("all_symbols")
            ),
            EnvVarArgs(
                name="BYBIT_TESTNET",
                value=sane_utils.get_var_for_target("bybit_testnet", default="0")
            )
        ]
    }
)


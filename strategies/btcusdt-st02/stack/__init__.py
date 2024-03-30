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

# my_topic = Topic.get(
#     "my-topic",
#     base_stack_ref.get_output(
#         "topics"
#     ).apply(
#         lambda topics: topics.get("my-topic").get("id")
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
        # "my-topic": my_topic,
    },
    datastore_id=f"projects/{sane_utils.get_project_id()}/databases/{sane_utils.get_var_for_target('project_name')}",
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="SYMBOL",
                value="BTCUSDT"
            ),
            EnvVarArgs(
                name="PROVIDER",
                value="BYBIT"
            ),
            EnvVarArgs(
                name="CATEGORY",
                value="LINEAR"
            ),
            EnvVarArgs(
                name="TAKER_FEE",
                value="0.00055"
            ),
            EnvVarArgs(
                name="LEVERAGE",
                value="10"
            ),
            EnvVarArgs(
                name="RESET_LIMIT_ON_EXIT",
                value="1"
            ),
            EnvVarArgs(
                name="SET_LIMIT_TO_SUPERTREND_INCLUDE_FEE",
                value="1"
            ),
            EnvVarArgs(
                name="MOCK_STRATEGY",
                value="1"
            ),
        ]
    }
)


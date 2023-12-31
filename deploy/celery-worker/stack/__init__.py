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

topic_scheduler_errors = Topic.get(
    "scheduler-errors",
    base_stack_ref.get_output(
        "topics"
    ).apply(
        lambda topics: topics.get("scheduler-errors").get("id")
    )
)

deployment = GkeDeployment(
    app_name,
    gcp_repository=gcp_repository,
    access_secrets=[
        "subjects_redis_url",
        "celery_broker",
        "celery_result_backend",
    ],
    publish_to={
        "scheduler-errors": topic_scheduler_errors,
    },
    use_firestore=True,
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="BYBIT_TESTNET",
                value=sane_utils.get_var_for_target("bybit_testnet", default="0")
            ),
            EnvVarArgs(
                name="KLINE_USE_CACHED_RESULTS",
                value=sane_utils.get_var_for_target("kline_use_cached_results", default="1")
            ),
            EnvVarArgs(
                name="KLINE_ALWAYS_CACHE_RESULTS",
                value=sane_utils.get_var_for_target("kline_always_cache_results", default="1")
            )
        ]
    }


)


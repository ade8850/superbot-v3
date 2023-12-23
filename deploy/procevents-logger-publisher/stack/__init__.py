import pulumi
import pulumi_gcp as gcp
from pulumi import Config
from pulumi_kubernetes.core.v1 import EnvVarArgs

from krules_dev import sane_utils
from krules_dev.sane_utils import get_stack_reference
from krules_dev.sane_utils.pulumi.components import GkeDeployment

# Initialize a config object
config = Config()

# Get the name of the "parent" stack that we will reference.
app_name = sane_utils.check_env("app_name")

base_stack_ref = get_stack_reference("base")

gcp_repository = gcp.artifactregistry.Repository.get(
    "gcp_repository",
    base_stack_ref.get_output(
        "docker-repository"
    ).apply(
        lambda repository: repository.get("id")
    )
)

topic_procevents = gcp.pubsub.Topic.get(
    "procevents",
    base_stack_ref.get_output(
        "topics"
    ).apply(
        lambda topics: topics.get("procevents").get("id")
    )
)


deployment = GkeDeployment(
    app_name,
    gcp_repository=gcp_repository,
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="LOGGER_NAME",
                value=sane_utils.name_resource("procevents")
            )
        ]
    },
    subscribe_to=[
        (
            "procevents",
            {
                "topic": topic_procevents.name,
                #"enable_exactly_once_delivery": True,
                "ack_deadline_seconds": 20,
            }
        ),
    ],
    use_firestore=True,
)

gcp.projects.IAMMember(
    "iam_log_writer",
    member=deployment.sa.sa.email.apply(
        lambda email: f"serviceAccount:{email}"
    ),
    project=sane_utils.get_project_id(),
    role="roles/logging.logWriter",
)



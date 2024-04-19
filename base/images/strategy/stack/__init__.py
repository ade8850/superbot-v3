import pulumi
from pulumi import Config
from pulumi_gcp.artifactregistry import Repository
from pulumi_gcp.pubsub import Topic
from pulumi_gcp.firestore import Database
from pulumi_kubernetes.core.v1 import EnvVarArgs

from krules_dev import sane_utils
from krules_dev.sane_utils import get_stack_reference
from krules_dev.sane_utils.pulumi.components import GkeDeployment, SaneDockerImage

config = Config()

app_name = sane_utils.check_env("app_name")

base_stack_ref = get_stack_reference("base")

gcp_repository = Repository.get(
    "gcp_repository",
    base_stack_ref.require_output("docker-repository.id")
)


strategy_base_image = SaneDockerImage(
    "strategy-image-base",
    gcp_repository=gcp_repository,
    context=".build/",
)

pulumi.export("strategy-image-base", strategy_base_image.image)
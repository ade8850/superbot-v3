import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as kubernetes
from pulumi import Config

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

deployment = GkeDeployment(
    app_name,
    service_type="ClusterIP",
    app_container_pvc_mounts={
        "data": {
            "storage": "2Gi",
            "mount_path": "/data",
        }
    },
    service_spec_kwargs={
        "ports": [
            kubernetes.core.v1.ServicePortArgs(
                name="redis",
                port=6379,
                protocol="TCP",
                target_port=6379
            ),
            kubernetes.core.v1.ServicePortArgs(
                name="insight",
                port=8001,
                protocol="TCP",
                target_port=8001
            ),
        ]
    },
    gcp_repository=gcp_repository,
)

pulumi.export("service", deployment.service)



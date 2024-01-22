import pulumi
import pulumi_gcp as gcp
import pulumi_kubernetes as kubernetes
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

deployment = GkeDeployment(
    app_name,
    service_type="ClusterIP",
    gcp_repository=gcp_repository,
    access_secrets=[
        "subjects_redis_url",
        "celery_broker",
    ],
    app_container_pvc_mounts={
        "jupyter-data": {
            "storage": "2Gi",
            "mount_path": "/root/work",
        }
    },
    service_spec_kwargs={
        "ports": [
            kubernetes.core.v1.ServicePortArgs(
                name="jupyterlab",
                port=8888,
                protocol="TCP",
                target_port=8888
            ),
        ]
    },
    use_firestore=True,
    app_container_kwargs={
        "env": [
            EnvVarArgs(
                name="COMPANION_ADDRESS",
                value=sane_utils.get_var_for_target("companion_address")
            ),
            EnvVarArgs(
                name="COMPANION_SUBSCRIPTION",
                value=sane_utils.get_var_for_target("companion_subscription")
            ),
            EnvVarArgs(
                name="COMPANION_APIKEY",
                value=sane_utils.get_var_for_target("companion_apikey")
            ),
            EnvVarArgs(
                name="ALL_SYMBOLS",
                value=sane_utils.get_var_for_target("all_symbols")
            ),
        ]
    }
)

pulumi.export("service", deployment.service)



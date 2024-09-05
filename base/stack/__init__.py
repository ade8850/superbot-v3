import pulumi
import pulumi_kubernetes as k8s
import pulumi_gcp as gcp

from krules_dev import sane_utils
from krules_dev.sane_utils.pulumi.components import (
    PubSubTopic,
    ArtifactRegistry, SaneDockerImage, FirestoreDB,
)

pulumi.export("topics.bybit_public.id", PubSubTopic("bybit-public").id)
pulumi.export("topics.procevents.id", PubSubTopic("procevents").id)
pulumi.export("topics.scheduler_errors.id", PubSubTopic("scheduler-errors").id)
pulumi.export("topics.companion_callbacks.id", PubSubTopic("companion-callbacks").id)

docker_registry = ArtifactRegistry(
    "docker-registry",
)
pulumi.export("docker-repository.id", docker_registry.repository.id)

namespace = k8s.core.v1.Namespace(
    "gke-namespace",
    metadata={
        "name": sane_utils.get_namespace()
    }
)
pulumi.export("gke-namespace", namespace)

ruleset_base_image = SaneDockerImage(
    "ruleset-base",
    gcp_repository=docker_registry.repository,
    context="base/images/ruleset",
)

pulumi.export("ruleset-image-base", ruleset_base_image.image)

# create kubernetes secrets from gcp secrets
celery_broker_secret = gcp.secretmanager.get_secret_version(
        project=sane_utils.get_project_id(),
        secret=sane_utils.name_resource("celery_broker"),
    )
celery_result_backend_secret = gcp.secretmanager.get_secret_version(
        project=sane_utils.get_project_id(),
        secret=sane_utils.name_resource("celery_result_backend"),
    )
subjects_redis_url_secret = gcp.secretmanager.get_secret_version(
        project=sane_utils.get_project_id(),
        secret=sane_utils.name_resource("subjects_redis_url"),
    )

k8s_secret = k8s.core.v1.Secret(
    "common-secrets",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="common-secrets"
    ),
    string_data={
        "celery_broker": pulumi.Output.secret(celery_broker_secret.secret_data),
        "celery_result_backend": pulumi.Output.secret(celery_result_backend_secret.secret_data),
        "subjects_redis_url": pulumi.Output.secret(subjects_redis_url_secret.secret_data)
    }
)

datastore = gcp.firestore.Database(
    "datastore",
    project=sane_utils.get_project_id(),
    name=sane_utils.get_var_for_target("project_name"),
    location_id=sane_utils.get_region(),
    type="DATASTORE_MODE",
    concurrency_mode="OPTIMISTIC",
    app_engine_integration_mode="DISABLED",
    # delete_protection_state="DELETE_PROTECTION_ENABLED",
    # deletion_policy="DELETE"
)



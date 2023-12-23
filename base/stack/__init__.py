import pulumi
import pulumi_kubernetes as kubernetes
import pulumi_gcp as gcp

from krules_dev import sane_utils
from krules_dev.sane_utils.pulumi.components import (
    PubSubTopic,
    ArtifactRegistry, SaneDockerImage, FirestoreDB,
)

topic_procevents = PubSubTopic("procevents")
topic_bybit_public = PubSubTopic("bybit-public")
topic_scheduler_errors = PubSubTopic("scheduler-errors")

pulumi.export("topics", {
    "procevents": topic_procevents,
    "bybit-public": topic_bybit_public,
    "scheduler-errors": topic_scheduler_errors,
})

docker_registry = ArtifactRegistry(
    "docker-registry",
)
pulumi.export("docker-repository", docker_registry.repository)

namespace = kubernetes.core.v1.Namespace(
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


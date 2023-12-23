import base64

import pulumi_kubernetes as kubernetes
from pulumi import Config, ResourceOptions

from krules_dev import sane_utils
from krules_dev.sane_utils import get_stack_reference

# Initialize a config object
config = Config()

app_name = sane_utils.check_env("app_name")
project_name = sane_utils.check_env("project_name")
target = sane_utils.get_target()

base_stack_ref = get_stack_reference("base")

cluster_name = f"{project_name}-db"

databases = sane_utils.check_env("databases").split(",")

secrets = []
for db in databases:
    secrets.append(
        kubernetes.core.v1.Secret(
            f"{db}-pg-secret",
            metadata=kubernetes.meta.v1.ObjectMetaArgs(
                name=f"{db}.{cluster_name}.credentials.postgresql.acid.zalan.do",
                labels={
                    "application": "spilo",
                    "cluster-name": cluster_name,
                    "team": "acid",
                },
            ),
            data={
                "username": base64.b64encode(db.encode()).decode(),
                "password": base64.b64encode(sane_utils.check_env("default_pg_password").encode()).decode()
            }
        )
    )


cluster = kubernetes.apiextensions.CustomResource(
    app_name,
    api_version="acid.zalan.do/v1",
    kind="postgresql",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        name=cluster_name,
    ),
    spec={
        "allowSourceRanges": None,
        "databases": {db: db for db in databases},
        "numberOfInstances": 1,
        "postgresql": {
            "version": "15",
        },
        "resources": {
            "limits": {
                "cpu": "500m",
                "memory": "500Mi",
            },
            "requests": {
                "cpu": "100m",
                "memory": "100Mi",
            },
        },
        "teamId": "acid",
        "users": {user: [] for user in databases},
        "volume": {
            "size": "10Gi"
        }
    },
    opts=ResourceOptions(depends_on=secrets),
)

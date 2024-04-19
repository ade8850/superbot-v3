#!/usr/bin/env python3

from sane import sane_run

from krules_dev import sane_utils
from krules_dev.sane_utils.pulumi.shell import get_stack_outputs

sane_utils.load_env()

app_name = sane_utils.check_env("APP_NAME")
project_name = sane_utils.check_env("PROJECT_NAME")
target = sane_utils.get_target()

strategy_base_outputs = get_stack_outputs("strategy-base")

sane_utils.make_prepare_build_context_recipes(
    image_base=strategy_base_outputs.get("strategy-image-base").get("repo_digest"),
    baselibs=[
    ],
    sources=[
        "requirements.txt",
        "ruleset.py",
        "ruleset_functions",
        "this_strategy.py",
    ],
)

sane_utils.make_pulumi_stack_recipes(
    app_name,
    configs={
        "gcp:project": sane_utils.get_var_for_target("project_id"),
        "kubernetes:context": sane_utils.get_var_for_target("kubectl_ctx", default=f"gke_{project_name}-{target}"),
        "base_stack": f"base-{target}",
    },
    up_deps=[
        ".build/Dockerfile"
    ]
)


# clean
sane_utils.make_clean_recipe(
    name="clean",
    globs=[
        ".build",
    ],
)

sane_run("pulumi_up")

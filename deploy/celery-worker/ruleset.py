import json
from pprint import pprint

from krules_core.base_functions.filters import Filter
from krules_core.base_functions.processing import Process
from krules_core.event_types import SUBJECT_PROPERTY_CHANGED
from krules_core.models import Rule

from app_common.ruleset_functions import CompanionPublish

rulesdata = [
    Rule(
        name="on-technical-analysis-value-change",
        subscribe_to=SUBJECT_PROPERTY_CHANGED,
        filters=[
            Filter(
                lambda payload: payload.get("property_name").startswith("ema_")
            )
        ],
        processing=[
            Process(
                lambda payload: print(json.dumps(payload, indent=2))
            ),
            CompanionPublish(
                properties=lambda payload: {
                    f'{payload.get("property_name")}_{key}':
                        value for key, value in payload.get("value").items()
                }
            )
        ]
    ),
]
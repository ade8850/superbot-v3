import json
from pprint import pprint
from typing import Sequence

from krules_core.base_functions.filters import Filter
from krules_core.base_functions.processing import Process
from krules_core.event_types import SUBJECT_PROPERTY_CHANGED
from krules_core.models import Rule

from strategy_common.ruleset_functions import CompanionPublish

rulesdata: Sequence[Rule] = [
    Rule(
        name="on-technical-analysis-dict-value-change",
        subscribe_to=SUBJECT_PROPERTY_CHANGED,
        filters=[
            Filter(
                lambda payload: any((
                    payload.get("property_name").startswith("ema_"),
                ))
            )
        ],
        processing=[
            # Process(
            #     lambda payload: print(json.dumps(payload, indent=2))
            # ),
            CompanionPublish(
                properties=lambda payload: {
                    f'{payload.get("property_name")}_{key}':
                        value for key, value in payload.get("value").items()
                }
            )
        ]
    ),
    Rule(
        name="on-technical-analysis-simple-value-change",
        subscribe_to=SUBJECT_PROPERTY_CHANGED,
        filters=[
            Filter(
                lambda payload: any((
                    payload.get("property_name").startswith("supertrend_"),
                ))
            )
        ],
        processing=[
            Process(
                lambda payload: print(json.dumps(payload, indent=2))
            ),
            CompanionPublish(
                properties=lambda payload: {
                    payload.get("property_name"): payload.get("value")
                }
            )
        ]
    ),
]
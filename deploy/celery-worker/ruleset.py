import json
from typing import Sequence

from krules_core.base_functions.filters import Filter
from krules_core.base_functions.processing import Process, ProcessingFunction
from krules_core.event_types import SUBJECT_PROPERTY_CHANGED
from krules_core.models import Rule

from celery_app.tasks import cm_publish


def _guess_entity_and_group_from_subject(subject_name):
    if subject_name.startswith('symbol:'):
        _, provider, category, symbol = subject_name.split(':')
        return symbol.upper(), f"symbols.{provider}.{category}"


class CompanionPublish(ProcessingFunction):

    def execute(self, entity=None, group=None, properties=None):

        if entity is None and group is None:
            entity, group = _guess_entity_and_group_from_subject(self.subject.name)

        if properties is None:
            properties = {}

        cm_publish.delay(
            entity=entity,
            group=group,
            properties=properties,
        )


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
                     payload.get("property_name"): payload.get("value")
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
            # Process(
            #     lambda payload: print(json.dumps(payload, indent=2))
            # ),
            CompanionPublish(
                properties=lambda payload: {
                    payload.get("property_name"): payload.get("value")
                }
            )
        ]
    ),

]

import json
from pprint import pprint

from krules_core.event_types import SUBJECT_PROPERTY_CHANGED
from krules_core.base_functions.processing import *
from krules_core.models import Rule

rulesdata = [
    Rule(
        name="on-technical-analysis-value-change",
        subscribe_to=SUBJECT_PROPERTY_CHANGED,
        processing=[
            Process(
                lambda payload: print(json.dumps(payload, indent=2))
            ),
        ]
    ),
]
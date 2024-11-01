import json
from datetime import datetime
from typing import List

from krules_core import event_types
from krules_core.base_functions.filters import Filter, OnSubjectPropertyChanged
from krules_core.base_functions.processing import Process, SetSubjectProperty
from krules_core.models import Rule

from datastore.ruleset_functions import DatastoreEntityStore
from strategy_common import mock
from strategy_common.ioc import container
from strategy_common.utils import calculate_pnl

implementation = container.implementation()

rulesdata: List[Rule] = [
    Rule(
        name="on-action-implements",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
        New action is set for Buy/Sell
        """,
        filters=[
            OnSubjectPropertyChanged("action", lambda new, old: new in ("Buy", "Sell")),
        ],
        processing=[
            Process(
                lambda self: implementation.on_action(
                    action=self.payload.get("value"),
                    price=self.subject.get("price")
                )
            ),
        ]
    ),
    Rule(
        name="on-limit-changed-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
        New action is set for Buy/Sell
        """,
        filters=[
            OnSubjectPropertyChanged(lambda name: name.startswith("limit_")),
        ],
        processing=[
            Process(
                lambda payload: implementation.strategy.publish(**{payload.get("property_name"): payload.get("value")})
            )
        ]
    ),
    Rule(
        name="mock-on-action-stop",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            [MOCK] Action stop, wait a second and then back to ready
            Also, save on datastore
        """,
        filters=[
            Filter(implementation.strategy.isMockStrategy),
            OnSubjectPropertyChanged("action", lambda value: value == "stop"),
        ],
        processing=[
            mock.UpdateMargin(lambda payload: payload.get("old_value"), sleep=2),
            SetSubjectProperty(
                "action", "ready", use_cache=False,
            ),
        ]
    ),
    Rule(
        name="on-action-change-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Action is changed, updates companion
        """,
        filters=[
            OnSubjectPropertyChanged("action", lambda value: value in ("Buy", "Sell", "stop")),
        ],
        processing=[
            Process(
                lambda self: (
                    implementation.strategy.publish(
                        action=self.payload.get("value"),
                        action_price=self.subject.get("price"),
                    ),
                    self.payload.get("value") in ("Buy", "Sell") and
                    implementation.strategy.position().publish(
                        action=self.payload.get("value"),
                        open_price=self.subject.get("price"),
                        open_time=datetime.utcnow().isoformat(),
                        open_values=json.dumps(implementation.values),
                        close_price=None,
                        close_values=None,
                    ) or implementation.strategy.position().publish(
                        action=self.payload.get("value"),
                        close_price=self.subject.get("price"),
                        close_values=json.dumps(implementation.values),
                    )
                )
            ),
        ]
    ),
    Rule(
        name="on-margin-change-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Action is changed, updates companion
        """,
        filters=[
            OnSubjectPropertyChanged("margin"),
        ],
        processing=[
            Process(
                lambda payload: (
                    implementation.strategy.position().publish(
                        margin=payload.get("value")
                    )
                )
            ),
        ]
    ),
    Rule(
        name="on-margin-change-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Margin is changed, updates companion
        """,
        filters=[
            OnSubjectPropertyChanged("margin"),
        ],
        processing=[
            Process(
                lambda self: implementation.strategy.publish(
                    margin=self.payload.get("value"),
                )
            ),
        ]
    ),
    Rule(
        name="on-change-side-implements",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Call the implementation class on side change
        """,
        filters=[
            OnSubjectPropertyChanged("side", lambda value: value in ("Buy", "Sell")),
            Filter(lambda self: self.payload.get("value") != self.subject.get("action"))
        ],
        processing=[
            Process(
                lambda payload: implementation.on_side(
                    side=payload.get("value"),
                    old_side=payload.get("old_value")
                )
            )
        ]
    ),
]

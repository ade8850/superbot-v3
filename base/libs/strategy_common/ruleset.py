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
            DatastoreEntityStore(
                "ActionTrack", key=lambda subject: subject.get("action_key"),
                properties=lambda self: dict(
                    strategy=implementation.strategy.name,
                    leverage=implementation.strategy.leverage,
                    side=self.payload.get("value"),
                    dt_open=datetime.utcnow(),
                    price_open=self.subject.get("price"),
                    margin=self.subject.get("margin")
                ),
                exclude_from_indexes=("price_open", "margin", "leverage"),
            )

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
    ## LEGACY ##################
    Rule(
        name="mock-on-action-stop-back-to-ready",
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
            DatastoreEntityStore(
                "ActionTrack", key=lambda subject: subject.get("action_key"),
                properties=lambda self: dict(
                    dt_close=datetime.utcnow(),
                    price_close=self.subject.get("price"),
                    new_margin=self.subject.get("margin"),
                    limit_price_reason=self.subject.get("limit_price_reason", default=None)
                ),
                exclude_from_indexes=("price_close", "new_margin"),
                update=True,
            ),
            SetSubjectProperty(
                "action", "ready", use_cache=False,
            ),
        ]
    ),
    # Rule(
    #     name="on-action-stop-cm-reset",
    #     subscribe_to=[
    #         event_types.SubjectPropertyChanged
    #     ],
    #     description="""
    #         Action stop, reset companion fields when limit does not reset
    #     """,
    #     filters=[
    #         Filter(not implementation.strategy.resetLimitOnExit),
    #         OnSubjectPropertyChanged("action", lambda value: value == "stop"),
    #     ],
    #     processing=[
    #         Process(
    #             lambda self: implementation.strategy.publish(
    #                 limit_price_reason="hold",
    #                 estimated_pnl=None,
    #                 limit_price=self.subject.get("limit_price", default=None)
    #             )
    #         ),
    #     ]
    # ),
    Rule(
        name="on-action-cm-publish",
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
                    self.payload.get("value") == "stop" and implementation.strategy.publish(
                        stop_reason=self.subject.get("action_stop_reason", default=None, use_cache=False)
                    ),
                )
            ),
        ]
    ),
    Rule(
        name="on-margin-cm-publish",
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
        name="on-change-side-reset-limit-price",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Reset limit_price on change direction
        """,
        filters=[
            OnSubjectPropertyChanged("side", lambda value: value in ("Buy", "Sell")),
            Filter(lambda self: self.payload.get("value") != self.subject.get("action"))
        ],
        processing=[
            SetSubjectProperty(
                "limit_price", lambda subejct: subejct.get("action_entry_price"), use_cache=False,
            ),
        ]
    ),
]

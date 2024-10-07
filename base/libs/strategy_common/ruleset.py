from datetime import datetime
from typing import List

from krules_core import event_types
from krules_core.base_functions.filters import Filter, OnSubjectPropertyChanged
from krules_core.base_functions.processing import Process, SetSubjectProperty, StoreSubject
from krules_core.models import Rule

from strategies.outer_limit_price import set_outer_limit_price
from strategy_common import mock
from strategy_common.ioc import container
from strategy_common.models import Strategy
from strategy_common.utils import calculate_pnl
from datastore.ruleset_functions import DatastoreEntityStore
from strategies.limit_price import set_limit_price

strategy: Strategy = container.strategy()

rulesdata: List[Rule] = [
    Rule(
        name="on-action-set-limit-price",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            New action is set for Buy/Sell, set limit price if null
        """,
        filters=[
            OnSubjectPropertyChanged("action", lambda new, old: new in ("Buy", "Sell")),
            Filter(lambda subject: subject.get("limit_price", default=None) in (None, 0))
        ],
        processing=[
            Process(
                lambda subject: set_limit_price(reason="action")
            ),
        ]
    ),
    Rule(
        name="on-action-set-outer-limit-price",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            New action is set for Buy/Sell, set outer limit price if null
        """,
        filters=[
            OnSubjectPropertyChanged("action", lambda new, old: new in ("Buy", "Sell")),
            Filter(lambda subject: subject.get("outer_limit_price", default=None) in (None, 0))
        ],
        processing=[
            Process(
                lambda subject: set_outer_limit_price(reason="action")
            ),
        ]
    ),
    Rule(
        name="on-limit-price-cm-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Limit price is changed, updates companion
        """,
        filters=[
            OnSubjectPropertyChanged("limit_price"),
        ],
        processing=[
            Process(
                lambda self: strategy.publish(
                    limit_price=self.payload.get("value"),
                    limit_price_reason=self.subject.get("limit_price_reason", default=None),
                    estimated_pnl=calculate_pnl(
                        price=self.payload.get("value"),
                    )
                )
            ),
        ]
    ),
    Rule(
        name="on-outer-limit-price-cm-publish",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Outer Limit price is changed, updates companion
        """,
        filters=[
            OnSubjectPropertyChanged("outer_limit_price"),
        ],
        processing=[
            Process(
                lambda self: strategy.publish(
                    outer_limit_price=self.payload.get("value"),
                    outer_limit_price_reason=self.subject.get("outer_limit_price_reason", default=None),
                    # estimated_pnl=calculate_pnl(
                    #     price=self.payload.get("value"),
                    # )
                )
            ),
        ]
    ),
    Rule(
        name="on-action-buysell",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Action is Buy/Sell, 
            - store price into subject
            - save direction in side property to allow to detect direction changes
            - create datastore ActionTrack entity
        """,
        filters=[
            OnSubjectPropertyChanged("action", lambda value: value in ("Buy", "Sell")),
        ],
        processing=[
            SetSubjectProperty(
                "action_entry_price", lambda subject: subject.get("price"), muted=True,
                use_cache=False,
            ),
            SetSubjectProperty(
                "side", lambda payload: payload.get("value"), use_cache=False,
            ),
            DatastoreEntityStore(
                "ActionTrack", key=lambda subject: subject.get("action_key"),
                properties=lambda self: dict(
                    strategy=strategy.name,
                    leverage=strategy.leverage,
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
        name="on-action-stop-reset-limit-price",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Action stop, reset limit price
        """,
        filters=[
            Filter(strategy.resetLimitOnExit),
            OnSubjectPropertyChanged("action", lambda value: value == "stop"),
        ],
        processing=[
            Process(lambda subject: set_limit_price(0, reason="action")),
            StoreSubject(),
        ]
    ),
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
            Filter(strategy.isMockStrategy),
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
    Rule(
        name="on-action-stop-cm-reset",
        subscribe_to=[
            event_types.SubjectPropertyChanged
        ],
        description="""
            Action stop, reset companion fields when limit does not reset
        """,
        filters=[
            Filter(not strategy.resetLimitOnExit),
            OnSubjectPropertyChanged("action", lambda value: value == "stop"),
        ],
        processing=[
            Process(
                lambda self: strategy.publish(
                    limit_price_reason="hold",
                    estimated_pnl=None,
                    limit_price=self.subject.get("limit_price", default=None)
                )
            ),
        ]
    ),
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
                    strategy.publish(
                        action=self.payload.get("value"),
                        action_price=self.subject.get("price"),
                    ),
                    self.payload.get("value") == "stop" and strategy.publish(
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
                lambda self: strategy.publish(
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

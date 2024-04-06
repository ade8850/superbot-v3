import os
import time
from datetime import datetime
from typing import List

from krules_core import event_types
from krules_core.base_functions.filters import Filter, OnSubjectPropertyChanged
from krules_core.base_functions.processing import Process, SetSubjectProperty, StoreSubject
from krules_core.models import Rule

from app_common.utils import calculate_pnl
from datastore.ruleset_functions import DatastoreEntityStore
from strategies import strategy
from strategies.limit_price import set_limit_price

from app_common import mock
from strategies.strategy import leverage, fee

RESET_LIMIT_ON_EXIT = bool(eval(os.environ.get('RESET_LIMIT_ON_EXIT', "1")))
MOCK_STRATEGY = bool(os.environ.get("MOCK_STRATEGY", "1"))

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
                lambda subject: set_limit_price(reason="action", subject=subject)
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
                        margin=self.subject.get("margin", default=100),
                        side=self.subject.get("action"),
                        leverage=leverage,
                        fee=fee,
                        entry_price=self.subject.get("action_entry_price"),
                        cur_price=self.payload.get("value"),
                    )
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
            Filter(RESET_LIMIT_ON_EXIT),
            OnSubjectPropertyChanged("action", lambda value: value == "stop"),
        ],
        processing=[
            Process(lambda subject: set_limit_price(0, reason="action", subject=subject)),
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
            Filter(MOCK_STRATEGY),
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
            Filter(not RESET_LIMIT_ON_EXIT),
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
]

from datetime import datetime
from pprint import pprint

import pytz
from krules_core.base_functions.processing import Process
from krules_core.models import Rule

from bybit.event_types import BybitStreams
from bybit.models import KlineMessage

rulesdata = [
    Rule(
        name="on-kline-received-dump-latency",
        subscribe_to=BybitStreams.KLINE,
        processing=[
            Process(
                lambda payload:
                    pprint(dict(
                        latency_ms=(
                            datetime.now(tz=pytz.UTC)-KlineMessage.model_validate(payload).ts
                        ).total_seconds() * 1000
                    ))
            )
        ],
    ),
]

from pprint import pprint

from krules_core.base_functions.filters import Filter
from krules_core.base_functions.processing import Process
from krules_core.models import Rule

from bybit.event_types import BybitStreams

rulesdata = [
    Rule(
        name="kline-receive-confirm",
        subscribe_to=BybitStreams.KLINE_DATA,
        filters=[
            Filter(
                  lambda payload: payload.get("data").confirm
            )
        ],
        processing=[
            Process(
                 lambda payload: pprint(payload.get("data").model_dump())
            ),
        ]
    ),
]

from datetime import timedelta
from typing import Sequence

from app_common.models import Interval

INTERVALS: Sequence[Interval] = (
    Interval(
        interval=timedelta(minutes=1),
        freq="T",
        name="1",
    ),
    Interval(
        interval=timedelta(minutes=3),
        freq="3T",
        name="3",
    ),
    Interval(
        interval=timedelta(minutes=5),
        freq="5T",
        name="5",
    ),
    Interval(
        interval=timedelta(minutes=15),
        freq="15T",
        name="15",
    ),
    Interval(
        interval=timedelta(minutes=30),
        freq="30T",
        name="30",
    ),
    Interval(
        interval=timedelta(hours=1),
        freq="H",
        name="60",
    ),
    Interval(
        interval=timedelta(hours=2),
        freq="2H",
        name="120",
    ),
    Interval(
        interval=timedelta(hours=4),
        freq="4H",
        name="240",
    ),
    Interval(
        interval=timedelta(hours=6),
        freq="6H",
        name="360",
    ),
    Interval(
        interval=timedelta(hours=12),
        freq="12H",
        name="720",
    ),
    Interval(
        interval=timedelta(hours=24),
        freq="D",
        name="D",
    ),
)


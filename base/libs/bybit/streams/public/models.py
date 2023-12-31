from datetime import datetime
from typing import Literal, List, Sequence, NamedTuple

from pydantic import BaseModel, field_validator, PositiveInt, field_serializer
from pydantic_core.core_schema import ValidationInfo


class BaseStreamMessage(BaseModel):
    topic: str
    ts: datetime
    type: Literal['snapshot', 'delta']

    @field_serializer('ts')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()


class BaseAPIResponse(BaseModel):
    retCode: int
    retMsg: str
    retExtInfo: dict
    time: datetime


class KlineMessageData(BaseModel):
    start: datetime
    end: datetime
    interval: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    turnover: float
    confirm: bool
    timestamp: datetime

    @field_serializer('start', 'end', 'timestamp')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()


class KlineMessage(BaseStreamMessage):
    data: Sequence[KlineMessageData]


class GetKlineAPIResponseResultListItem(NamedTuple):
    start: datetime
    open: float
    close: float
    high: float
    low: float
    volume: float
    turnover: float

    def get_time(self) -> str:
        """
        round start to minute
        """
        return datetime(
            year=self.start.year,
            month=self.start.month,
            day=self.start.day,
            hour=self.start.hour,
            minute=self.start.minute,
            tzinfo=self.start.tzinfo
        ).isoformat()


class GetKlineAPIResponseResult(BaseModel):
    symbol: str
    category: str
    list: Sequence[GetKlineAPIResponseResultListItem]


class GetKlineAPIResponse(BaseAPIResponse):
    result: GetKlineAPIResponseResult


class TickerMessageData(BaseModel):
    symbol: str
    tickDirection: str
    price24hPcnt: str
    lastPrice: float
    prevPrice24h: float
    highPrice24h: float
    lowPrice24h: float
    prevPrice1h: float
    markPrice: float
    indexPrice: float
    openInterest: float
    openInterestValue: float
    turnover24h: float
    volume24h: float
    nextFundingTime: datetime
    fundingRate: float
    bid1Price: float
    bid1Size: float
    ask1Price: float
    ask1Size: float


class TickerMessage(BaseStreamMessage):
    cs: int
    data: TickerMessageData

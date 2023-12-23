from datetime import datetime
from typing import Literal, List

from pydantic import BaseModel, field_validator, PositiveInt, field_serializer
from pydantic_core.core_schema import ValidationInfo


class BaseStreamMessage(BaseModel):
    topic: str
    ts: datetime
    type: Literal['snapshot', 'delta']

    # @field_validator('ts')
    # @classmethod
    # def validate_ts(cls, v: PositiveInt, info: ValidationInfo) -> datetime:
    #     return datetime.fromtimestamp(v / 1000)

    @field_serializer('ts')
    def serialize_dt(self, dt: datetime, _info):
        return dt.timestamp()


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
    data: List[KlineMessageData]


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

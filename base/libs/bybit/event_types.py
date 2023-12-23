from krules_core.models import EventType


class BybitStreams:

    KLINE = EventType("bybit.streams.public.kline")
    KLINE_DATA = EventType("bybit.streams.public.kline.data")
    TICKER = EventType("bybit.streams.public.ticker")

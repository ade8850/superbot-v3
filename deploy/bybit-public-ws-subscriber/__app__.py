import re
from datetime import datetime

import pytz
from krules_core.providers import event_router_factory
from krules_fastapi_env import KrulesApp
from contextlib import asynccontextmanager

from pytz import tzinfo

from bybit.event_types import BybitStreams
from bybit.streams import public
import os
from pybit.unified_trading import WebSocket

from bybit.streams.public.models import KlineMessage, TickerMessage

ws: WebSocket | None = None

symbols = os.environ.get("SUBSCRIBE_SYMBOLS").split(",")
kline = bool(eval(os.environ.get("SUBSCRIBE_KLINE")))
ticker = bool(eval(os.environ.get("SUBSCRIBE_TICKER")))

event_router = event_router_factory()

re_kline_topic = re.compile("^kline.1.([A-Z0-9]+)$")


@asynccontextmanager
async def lifespan(app: KrulesApp):
    def _handle_ticker(raw_message):
        try:
            message = TickerMessage.model_validate(raw_message)
            latency_ms = (datetime.now(tz=pytz.UTC)-message.ts).total_seconds() * 1000
            symbol = message.topic.rsplit(".")[-1].lower()
            event_router.route(
                BybitStreams.TICKER,
                f"symbol:bybit:perpetual:{symbol}",
                message.model_dump(),
                topic=os.environ["BYBIT_PUBLIC_TOPIC"]
            )
            app.logger.info(message, extra={"props": {"latency_ms": latency_ms}})
        except Exception as ex:
            app.logger.exception(ex)

    def _handle_kline(raw_message: dict):
        try:
            message = KlineMessage.model_validate(raw_message)
            latency_ms = (datetime.now(tz=pytz.UTC)-message.ts).total_seconds() * 1000
            symbol = message.topic.rsplit(".")[-1].lower()
            event_router.route(
                BybitStreams.KLINE,
                f"symbol:bybit:perpetual:{symbol}",
                message.model_dump(),
                topic=os.environ["BYBIT_PUBLIC_TOPIC"]
            )
            app.logger.info(message, extra={"props": {"latency_ms": latency_ms}})
        except Exception as ex:
            app.logger.exception(ex)

    global ws
    ws = WebSocket(
        channel_type="linear",
        testnet=False
    )

    for symbol in symbols:
        if kline and False:
            app.logger.info("Subscribing KLINE stream", extra={"props": {"symbol": symbol}})
            ws.kline_stream(
                interval=1,
                symbol=symbol,
                callback=_handle_kline
            )
        if ticker:
            app.logger.info("Subscribing TICKER stream", extra={"props": {"symbol": symbol}})
            ws.ticker_stream(
                symbol=symbol,
                callback=_handle_ticker
            )
    yield
    # shutdown


app = KrulesApp(lifespan=lifespan)


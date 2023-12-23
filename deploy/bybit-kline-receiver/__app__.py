import re
from datetime import datetime

import pytz
from contexttimer import Timer
from krules_core.providers import event_router_factory, event_dispatcher_factory
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


@asynccontextmanager
async def lifespan(app: KrulesApp):
    def _handle_kline(raw_message: dict):
        try:
            with Timer(factor=1000) as t:
                message = KlineMessage.model_validate(raw_message)
                latency_ms = (datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000
                symbol = message.topic.rsplit(".")[-1].lower()
                app.logger.info(f">received {symbol}", extra={"props": {"latency_ms": latency_ms}})
                for data in message.data:
                    event_router_factory().route(
                        BybitStreams.KLINE_DATA,
                        f"symbol:bybit:perpetual:{symbol}",
                        {
                            "data": data,
                        }
                    )
            app.logger.info(f"<processed {symbol}", extra={"props": {"elapsed": t.elapsed}})
        except Exception as ex:
            app.logger.exception(ex)

    global ws
    ws = WebSocket(
        channel_type="linear",
        testnet=False
    )

    for symbol in symbols:
        app.logger.info("Subscribing KLINE stream", extra={"props": {"symbol": symbol}})
        ws.kline_stream(
            interval=1,
            symbol=symbol,
            callback=_handle_kline
        )
    yield
    # shutdown


app = KrulesApp(lifespan=lifespan)

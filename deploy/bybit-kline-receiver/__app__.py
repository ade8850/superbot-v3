import os
from contextlib import asynccontextmanager
from datetime import datetime

import pytz
from contexttimer import Timer
from krules_fastapi_env import KrulesApp
from pybit.unified_trading import WebSocket

from app_common.models import Symbol
from bybit import INTERVALS
from bybit.streams.public.models import KlineMessage
from celery_app.tasks import bybit_process_kline_data

ws: WebSocket | None = None

symbols = os.environ.get("SUBSCRIBE_SYMBOLS").split(",")


@asynccontextmanager
async def lifespan(app: KrulesApp):
    def _handle_kline(raw_message: dict):
        try:
            with Timer(factor=1000) as t:
                message = KlineMessage.model_validate(raw_message)
                latency_ms = (datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000
                symbol = Symbol(
                    name=message.topic.rsplit(".")[-1],
                    category="linear",
                    provider="bybit",
                )
                app.logger.info(f">received {symbol}", extra={"props": {"latency_ms": latency_ms}})
                for data in message.data:
                    if data.confirm:
                        app.logger.info(f">CONFIRMED [{symbol}]<")
                        for interval in INTERVALS:
                            bybit_process_kline_data.delay(
                                interval=interval,
                                symbol=symbol,
                                kline_data=data,
                            )
            app.logger.info(f"<processed {symbol}", extra={"props": {"elapsed_ms": t.elapsed}})
        except Exception as ex:
            app.logger.exception(ex)

    global ws
    ws = WebSocket(
        channel_type="linear",
        testnet=bool(eval(os.environ.get("BYBIT_TESTNET", "0")))
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

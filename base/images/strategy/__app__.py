import importlib
import os
from contextlib import asynccontextmanager
from datetime import datetime

import pytz
from pybit.unified_trading import WebSocket

from bybit.models import TickerMessage
from krules_fastapi_env import KrulesApp
from strategies import strategy
from strategies.common.action import set_action

ws: WebSocket | None = None

subject = strategy.get_subject()

this_strategy = importlib.import_module("this_strategy")

@asynccontextmanager
async def lifespan(app: KrulesApp):
    def _handle_ticker(raw_message):
        try:
            message: TickerMessage = TickerMessage.parse_obj(raw_message)
            latency_ms = (datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000
            if (action := subject.get("action", default=None)) is None:
                action = "ready"
                subject.m_action = action
            price, old_price = subject.set("price", message.data.markPrice, muted=True)
            if price != old_price:
                strategy_results = this_strategy.perform(price, subject)
                processing_ms = ((datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000) - latency_ms
                app.logger.info(message.topic,
                                extra={"props": {
                                    "action": action,
                                    "latency_ms": round(latency_ms, 2), "processing_ms": round(processing_ms, 2),
                                    "strategy": strategy_results
                                }})
            if action == "ready" and subject.get("verb") in ("Buy", "Sell"):
                action = set_action(subject.get("verb"), reason="verb", subject=subject)

                app.logger.info(f"Action set to {action}")
        except Exception as ex:
            app.logger.exception(ex)

    global ws
    ws = WebSocket(
        channel_type="linear",
        testnet=False
    )

    symbol = os.environ["SYMBOL"]
    app.logger.info("Subscribing TICKER stream", extra={"props": {"symbol": symbol}})
    ws.ticker_stream(
        symbol=symbol,
        callback=_handle_ticker
    )

    yield

    # shutdown
    ws.exit()


app = KrulesApp(lifespan=lifespan)

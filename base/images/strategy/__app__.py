import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime

import pytz
import rich
from pybit.unified_trading import WebSocket
from rich.pretty import pprint

from bybit.models import TickerMessage
from krules_fastapi_env import KrulesApp

from strategies.outer_limit_price import set_outer_limit_price
from strategy_common.action import set_action

from pubsub_subscriber import PubSubSubscriber

import this_strategy

from strategy_common.ioc import container

strategy = container.strategy()


def _handle_ticker(app, raw_message):
    try:
        subject = strategy.get_subject()
        message: TickerMessage = TickerMessage.parse_obj(raw_message)
        latency_ms = (datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000
        if (action := subject.get("action", default=None)) is None:
            action = "ready"
            subject.m_action = action
        price, old_price = subject.set("price", message.data.markPrice, muted=True)
        if price != old_price:
            strategy_results = this_strategy.perform(price)
            processing_ms = ((datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000) - latency_ms
            rich.pretty.pprint({"topic": message.topic,
                                "action": action,
                                "latency_ms": round(latency_ms, 2),
                                "processing_ms": round(processing_ms, 2),
                                "strategy": strategy_results
                                })
        if action == "ready" and subject.get("verb") in ("Buy", "Sell"):
            action = set_action(subject.get("verb"), reason="verb")

            app.logger.debug(f"Action set to {action}")
    except Exception as ex:
        app.logger.exception(ex)


ws = WebSocket(
    channel_type="linear",
    testnet=False
)


async def on_minute_scheduler():
    while True:
        this_strategy.on_minute()
        await asyncio.sleep(60)


async def _handle_pubsub(message):
    data = json.loads(message.data)

    pprint(data)

    subject = strategy.get_subject()

    outer_limit_price = subject.get("outer_limit_price", default=None)
    cur_price = subject.get("price")
    if outer_limit_price is None:
        rich.print("No outer_limit_price")
        return

    diff = data.get("value") - data.get("old_value")
    new_outer_limit_price = outer_limit_price + diff
    changed = False
    if cur_price > outer_limit_price:
        if diff > 0:
            rich.print(f"[green]++ increase outer_limit_price to {new_outer_limit_price}[/green]")
            set_outer_limit_price(new_outer_limit_price, "follow")
            changed = True
    elif cur_price < outer_limit_price:
        if diff < 0:
            rich.print(f"[red]-- decrease outer_limit_price to {new_outer_limit_price}[/red]")
            set_outer_limit_price(new_outer_limit_price, "follow")
            changed = True

    if not changed:
        rich.print(f"[grey85]== outer_limit_price is stable[/grey85]")


@asynccontextmanager
async def lifespan(app: KrulesApp):
    global ws
    symbol = strategy.symbol.name.upper()
    app.logger.info(f"Connect to stream for symbol {symbol} using strategy {strategy.name}")
    ws.ticker_stream(
        symbol=symbol,
        callback=lambda raw_message: _handle_ticker(app, raw_message)
    )

    pubsub_subscriber: PubSubSubscriber | None = None
    if strategy.outerLimitFollows is not None:
        pubsub_subscriber = PubSubSubscriber(app)

        pattern = f"^signal:bybit:perpetual:{symbol.lower()}:{strategy.outerLimitFollows}$"
        app.logger.info(f"Subscribe to {pattern}")
        pubsub_subscriber.add_process_function_for_subject(
            pattern, _handle_pubsub
        )

        await pubsub_subscriber.start()

    _ = asyncio.create_task(on_minute_scheduler())

    yield

    if pubsub_subscriber is not None:
        await pubsub_subscriber.stop()

    ws.exit()


app = KrulesApp(lifespan=lifespan, wrap_subjects=False)

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


from strategy_common.ioc import container

implementation = container.implementation()

from rich.console import Console
from rich.traceback import Traceback

console = Console()


def _handle_ticker(app, raw_message):
    try:
        subject = implementation.strategy.get_subject()
        message: TickerMessage = TickerMessage.parse_obj(raw_message)
        latency_ms = (datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000
        action = subject.get("action", default=None)
        if action not in ("Buy", "Sell", "ready", "stop"):
            console.print("NO ACTION > SKIP")
            return
        price, old_price = subject.set("price", message.data.markPrice, muted=True)
        if price != old_price:
            implementation.session(price)
            if action in ('Buy', 'Sell') and implementation.check_close(action):
                set_action("stop", reason="strategy")
            elif action == "ready":
                if (verb := implementation.get_common_verb()) in ('Buy', 'Sell'):
                    set_action(verb, reason="strategy")
            processing_ms = ((datetime.now(tz=pytz.UTC) - message.ts).total_seconds() * 1000) - latency_ms
            rich.pretty.pprint({"topic": message.topic,
                                "action": action,
                                "latency_ms": round(latency_ms, 2),
                                "processing_ms": round(processing_ms, 2),
                                "__all__": implementation.values["__all__"],
                                })
    except Exception as ex:
        tb = Traceback.from_exception(type(ex), ex, ex.__traceback__)
        console.print(tb)
        implementation.strategy.publish(last_error=str(ex), last_error_tb=str(tb))


ws: WebSocket = WebSocket(
    channel_type="linear",
    testnet=False
)


async def on_minute_scheduler():
    while True:
        implementation.on_minute()
        await asyncio.sleep(60)


async def _handle_pubsub(message, indicator):
    data = json.loads(message.data)

    implementation.on_indicator(indicator, **data)

    # LEGACY
    subject = implementation.strategy.get_subject()

    outer_limit_price = subject.get("outer_limit_price", default=None)
    if not outer_limit_price:
        return
    cur_price = subject.get("price")

    diff = data.get("value") - data.get("old_value")
    new_outer_limit_price = outer_limit_price + diff
    changed = False
    if cur_price > outer_limit_price:
        if diff > 0:
            #console.print(f"[green]++ increase outer_limit_price to {new_outer_limit_price}[/green]")
            set_outer_limit_price(new_outer_limit_price, "follow")
            changed = True
    elif cur_price < outer_limit_price:
        if diff < 0:
            #console.print(f"[red]-- decrease outer_limit_price to {new_outer_limit_price}[/red]")
            set_outer_limit_price(new_outer_limit_price, "follow")
            changed = True

    #if not changed:
    #    rich.print(f"[grey85]== outer_limit_price is stable[/grey85]")
    ########


@asynccontextmanager
async def lifespan(app: KrulesApp):
    global ws
    strategy = implementation.strategy
    symbol = strategy.symbol.name.upper()
    app.logger.info(f"Connect to stream for symbol {symbol} using strategy {strategy.name}")
    ws.ticker_stream(
        symbol=symbol,
        callback=lambda raw_message: _handle_ticker(app, raw_message)
    )

    pubsub_subscriber: PubSubSubscriber | None = None
    if strategy.outerLimitFollows is not None:
        pubsub_subscriber = PubSubSubscriber(app)

        pattern = f"^signal:bybit:perpetual:{symbol.lower()}:(?P<indicator>.*)$"
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

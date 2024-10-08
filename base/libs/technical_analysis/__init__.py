import os
from typing import Sequence, List, Mapping, Any, Tuple

import pandas as pd
import pandas_ta
from krules_core.providers import event_router_factory

from app_common.models import Interval, Symbol

from rich.pretty import pprint

event_router = event_router_factory()


class TechnicalAnalysis:
    def __init__(self, df: pd.DataFrame, interval: Interval, symbol: Symbol):
        self.df = df
        self.symbol = symbol
        self.interval = interval

    def run(self):
        signals: List[Tuple[str, Any, Any]] = [  # signal, value, old_value
            *self.calculate_emas(periods=[
                100, 200
            ]),
            *self.calculate_supertrend(length=10, multiplier=3)
        ]

        # self.calculate_stochastic_rsi(window=14, smooth1=3, smooth2=3)
        pprint(signals)
        for signal in signals:
            event_router.route(
                "ta.signal",
                f"signal:bybit:perpetual:{self.symbol.name.lower()}:{signal[0]}",
                {
                    "value": signal[1],
                    "old_value": signal[2],
                },
                topic=os.environ["SIGNALS_TOPIC"]
            )

    def calculate_emas(self, periods: Sequence[int]) -> Tuple[str, Any, Any]:
        from ta.trend import EMAIndicator

        emas = {}
        for period in periods:
            ema = EMAIndicator(self.df['close'], window=period)
            self.df[f"ema_{period}"] = ema.ema_indicator()
            emas[period] = self.df.iloc[-1][f"ema_{period}"]

        for period, value in emas.items():
            signal = f"ema_{period}_{self.interval.freq}"
            value, old_value = self.symbol.get_subject().set(signal, emas[period], use_cache=False)
            yield signal, value, old_value

    def calculate_stochastic_rsi(self, window, smooth1, smooth2) -> Tuple[str, Any, Any]:
        from ta.momentum import StochRSIIndicator

        stochastic_rsi_indicator = StochRSIIndicator(close=self.df["close"], window=window, smooth1=smooth1,
                                                     smooth2=smooth2)
        self.df["stochrsi"] = stochastic_rsi_indicator.stochrsi()
        self.df["stochrsi_d"] = stochastic_rsi_indicator.stochrsi_d()
        self.df["stochrsi_k"] = stochastic_rsi_indicator.stochrsi_k()
        row = self.df.iloc[-1]

        signal = f"stochrsi_{self.interval.freq}"
        value, old_value = self.symbol.get_subject().set(signal, {
            "v": row["stochrsi"],
            "d": row['stochrsi_d'],
            "k": row['stochrsi_k'],
        }, use_cache=False, muted=True)
        yield signal, value, old_value

    def calculate_supertrend(self, length, multiplier) -> Tuple[str, Any, Any]:
        ta_res = pandas_ta.supertrend(high=self.df['high'], low=self.df['low'], close=self.df['close'],
                                      length=length, multiplier=multiplier)
        self.df["supertrend"] = ta_res[f'SUPERT_{length}_{multiplier}.0']
        self.df["supertrend_d"] = ta_res[f'SUPERTd_{length}_{multiplier}.0']

        row = self.df.iloc[-1]
        #signals: List[Tuple[str, Any, Any]] = []
        signal = f"supertrend_{self.interval.freq}"
        value, old_value = self.symbol.get_subject().set(signal, float(row['supertrend']), use_cache=False)
        #signals.append((signal, value, old_value))
        yield signal, value, old_value
        signal = f"supertrend_dir_{self.interval.freq}"
        value, old_value = self.symbol.get_subject().set(signal, int(row['supertrend_d']), use_cache=False)
        #signals.append((signal, value, old_value))
        yield signal, value, old_value
        #return signals



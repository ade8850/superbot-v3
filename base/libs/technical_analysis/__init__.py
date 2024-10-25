import os
from typing import Sequence, List, Mapping, Any, Tuple

import numpy as np
import pandas as pd
import pandas_ta
#from stock_indicators import Quote, indicators

from krules_core.providers import event_router_factory

from app_common.models import Interval, Symbol

from rich.pretty import pprint

event_router = event_router_factory()


def tv_supertrend(high, low, close, open, length=10, multiplier=3.0):
    """
    Supertrend implementation matching TradingView's approach with pandas_ta compatible keys
    """

    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.rolling(window=length).mean()

    # Calculate price basis as (high + low)/2
    price_basis = (high + low) / 2

    # Calculate upper and lower bands
    upperband = price_basis + (multiplier * atr)
    lowerband = price_basis - (multiplier * atr)

    # Initialize Supertrend
    m = len(close)
    dir_, trend = [1] * m, [0] * m
    long, short = [np.nan] * m, [np.nan] * m

    # Calculate Supertrend
    for i in range(1, m):
        if close.iloc[i] > upperband.iloc[i - 1]:
            dir_[i] = 1
        elif close.iloc[i] < lowerband.iloc[i - 1]:
            dir_[i] = -1
        else:
            dir_[i] = dir_[i - 1]
            if dir_[i] > 0 and lowerband.iloc[i] < lowerband.iloc[i - 1]:
                lowerband.iloc[i] = lowerband.iloc[i - 1]
            if dir_[i] < 0 and upperband.iloc[i] > upperband.iloc[i - 1]:
                upperband.iloc[i] = upperband.iloc[i - 1]

        if dir_[i] > 0:
            trend[i] = long[i] = lowerband.iloc[i]
        else:
            trend[i] = short[i] = upperband.iloc[i]

    # Prepare DataFrame with pandas_ta compatible keys
    _props = f"_{length}_{multiplier}"
    df = pd.DataFrame({
        f"SUPERT{_props}": trend,
        f"SUPERTd{_props}": dir_,
        f"SUPERTl{_props}": long,
        f"SUPERTs{_props}": short,
    }, index=close.index)

    df.name = f"SUPERT{_props}"

    return df

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
            *self.calculate_supertrend(length=16, multiplier=5)
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
        ta_res = tv_supertrend(high=self.df['high'], low=self.df['low'], close=self.df['close'], open=self.df['open'],
                               length=length, multiplier=multiplier)
        self.df["supertrend"] = ta_res[f'SUPERT_{length}_{multiplier}']
        self.df["supertrend_d"] = ta_res[f'SUPERTd_{length}_{multiplier}']

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

    # def calculate_supertrend(self, length: int = 14, multiplier: float = 3.0) -> Tuple[str, Any, Any]:
    #     """
    #     Calculate Supertrend indicator using stock_indicators library
    #
    #     Args:
    #         length: Lookback period for ATR calculation (default: 14)
    #         multiplier: ATR multiplier (default: 3.0)
    #
    #     Returns:
    #         Generator yielding signal tuples (signal_name, current_value, old_value)
    #     """
    #     # Convert DataFrame to Quote objects
    #     quotes_list = [
    #         Quote(d, o, h, l, c, v)
    #         for d, o, h, l, c, v
    #         in zip(
    #             self.df.index,  # Using index as date
    #             self.df['open'],
    #             self.df['high'],
    #             self.df['low'],
    #             self.df['close'],
    #             self.df['volume'] if 'volume' in self.df else [0] * len(self.df)  # Handle missing volume
    #         )
    #     ]
    #
    #     # Calculate SuperTrend
    #     results = indicators.get_super_trend(quotes_list, length, multiplier)
    #
    #     # Convert results to DataFrame columns
    #     self.df['supertrend'] = [result.super_trend for result in results]
    #
    #     # Calculate trend direction based on band position relative to close
    #     # 1 when close > supertrend (bullish), -1 when close < supertrend (bearish)
    #     self.df['supertrend_d'] = [
    #         1 if (pd.notna(result.super_trend) and
    #               self.df['close'].iloc[i] > result.super_trend)
    #         else -1 if pd.notna(result.super_trend)
    #         else 0  # for initial None values
    #         for i, result in enumerate(results)
    #     ]
    #
    #     # Generate signals from last row
    #     row = self.df.iloc[-1]
    #
    #     # Yield supertrend value signal
    #     signal = f"supertrend_{self.interval.freq}"
    #     value, old_value = self.symbol.get_subject().set(
    #         signal,
    #         float(row['supertrend']) if pd.notna(row['supertrend']) else 0.0,
    #         use_cache=False
    #     )
    #     yield signal, value, old_value
    #
    #     # Yield supertrend direction signal
    #     signal = f"supertrend_dir_{self.interval.freq}"
    #     value, old_value = self.symbol.get_subject().set(
    #         signal,
    #         int(row['supertrend_d']),
    #         use_cache=False
    #     )
    #     yield signal, value, old_value

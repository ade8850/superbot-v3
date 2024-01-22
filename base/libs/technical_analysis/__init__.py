from typing import Sequence

import numpy as np
import pandas as pd

from app_common.models import Interval, Symbol


class TechnicalAnalysis:
    def __init__(self, df: pd.DataFrame, interval: Interval, symbol: Symbol):
        self.df = df
        self.symbol = symbol
        self.interval = interval

    def run(self):
        self.calculate_emas(periods=[
            #9, 12, 26, 50, 100, 200
            100
        ])
        #self.calculate_stochastic_rsi(window=14, smooth1=3, smooth2=3)
        #self.calculate_supertrend(lookback=10, multiplier=3)

    def calculate_emas(self, periods: Sequence[int]):
        from ta.trend import EMAIndicator

        emas = {}
        for period in periods:
            ema = EMAIndicator(self.df['close'], window=period)
            self.df[f"ema_{period}"] = ema.ema_indicator()
            emas[period] = self.df.iloc[-1][f"ema_{period}"]

        self.symbol.get_subject().set(f"ema_{self.interval.freq}", emas, use_cache=False)

    def calculate_stochastic_rsi(self, window, smooth1, smooth2):
        from ta.momentum import StochRSIIndicator

        stochastic_rsi_indicator = StochRSIIndicator(close=self.df["close"], window=window, smooth1=smooth1,
                                                     smooth2=smooth2)
        self.df["stochrsi"] = stochastic_rsi_indicator.stochrsi()
        self.df["stochrsi_d"] = stochastic_rsi_indicator.stochrsi_d()
        self.df["stochrsi_k"] = stochastic_rsi_indicator.stochrsi_k()
        row = self.df.iloc[-1]

        self.symbol.get_subject().set(f"stochrsi_{self.interval.freq}", {
            "v": row["stochrsi"],
            "d": row['stochrsi_d'],
            "k": row['stochrsi_k'],
        }, use_cache=False)

    def calculate_supertrend(self, lookback, multiplier):
        df = self.df
        high = df['high']
        low = df['low']
        close = df['close']
        # ATR
        tr1 = pd.DataFrame(high - low)
        tr2 = pd.DataFrame(abs(high - close.shift(1)))
        tr3 = pd.DataFrame(abs(low - close.shift(1)))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
        atr = tr.ewm(lookback).mean()

        # H/L AVG AND BASIC UPPER & LOWER BAND
        hl_avg = (high + low) / 2
        upper_band = (hl_avg + multiplier * atr).dropna()
        lower_band = (hl_avg - multiplier * atr).dropna()

        # FINAL UPPER BAND
        final_bands = pd.DataFrame(columns=['upper', 'lower'])
        final_bands.iloc[:, 0] = [x for x in upper_band - upper_band]
        final_bands.iloc[:, 1] = final_bands.iloc[:, 0]

        for i in range(len(final_bands)):
            if i == 0:
                final_bands.iloc[i, 0] = 0
            else:
                if (upper_band.iloc[i] < final_bands.iloc[i - 1, 0]) | (close.iloc[i - 1] > final_bands.iloc[i - 1, 0]):
                    final_bands.iloc[i, 0] = upper_band.iloc[i]
                else:
                    final_bands.iloc[i, 0] = final_bands.iloc[i - 1, 0]

        # FINAL LOWER BAND
        for i in range(len(final_bands)):
            if i == 0:
                final_bands.iloc[i, 1] = 0
            else:
                if (lower_band.iloc[i] > final_bands.iloc[i - 1, 1]) | (close.iloc[i - 1] < final_bands.iloc[i - 1, 1]):
                    final_bands.iloc[i, 1] = lower_band.iloc[i]
                else:
                    final_bands.iloc[i, 1] = final_bands.iloc[i - 1, 1]

        # SUPERTREND
        supertrend = pd.DataFrame(columns=[f'supertrend_{lookback}'])
        supertrend.iloc[:, 0] = [x for x in final_bands['upper'] - final_bands['upper']]

        for i in range(len(supertrend)):
            if i == 0:
                supertrend.iloc[i, 0] = 0
            elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and close.iloc[i] < final_bands.iloc[i, 0]:
                supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
            elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 0] and close.iloc[i] > final_bands.iloc[i, 0]:
                supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
            elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and close.iloc[i] > final_bands.iloc[i, 1]:
                supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
            elif supertrend.iloc[i - 1, 0] == final_bands.iloc[i - 1, 1] and close.iloc[i] < final_bands.iloc[i, 1]:
                supertrend.iloc[i, 0] = final_bands.iloc[i, 0]

        supertrend = supertrend.set_index(upper_band.index)
        supertrend = supertrend.dropna()[1:]

        # ST UPTREND/DOWNTREND
        upt = []
        dt = []
        close = close.iloc[len(close) - len(supertrend):]

        for i in range(len(supertrend)):
            if close.iloc[i] > supertrend.iloc[i, 0]:
                upt.append(supertrend.iloc[i, 0])
                dt.append(np.nan)
            elif close.iloc[i] < supertrend.iloc[i, 0]:
                upt.append(np.nan)
                dt.append(supertrend.iloc[i, 0])
            else:
                upt.append(np.nan)
                dt.append(np.nan)

        # st, upt, dt = pd.Series(supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
        # upt.index, dt.index = supertrend.index, supertrend.index
        #
        # df['st'], df['st_upt'], df['st_dt'] = st, upt, dt
        st = pd.Series(supertrend.iloc[:, 0])

        df['st'] = st
        st = df.iloc[-1].st
        self.symbol.get_subject().set(f"st_{self.interval.freq}", st, use_cache=False)


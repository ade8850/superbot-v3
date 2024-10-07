import base64
import io
import json
import os
from typing import List

import pandas as pd
from pybit.unified_trading import HTTP

from  app_common.models import Interval, Symbol
from bybit.models import KlineMessageData, GetKlineAPIResponse, GetInstrumentInfoAPIResponse
from technical_analysis import TechnicalAnalysis

kline_use_cached_results = bool(eval(os.environ.get("KLINE_USE_CACHED_RESULTS", "1")))
kline_always_cache_results = bool(eval(os.environ.get("KLINE_ALWAYS_CACHE_RESULTS", "0")))
kline_store_df_on_subject = bool(eval(os.environ.get("KLINE_STORE_DF_ON_SUBJECT", "0")))
kline_limit_size = int(eval(os.environ.get("KLINE_LIMIT_SIZE", "400")))


def _get_session() -> HTTP:
    return HTTP(testnet=bool(eval(os.environ.get("BYBIT_TESTNET", "0"))))


def process_kline_data(task, interval: dict, symbol: dict, kline_data: dict):
    interval = Interval.model_validate(interval)
    symbol = Symbol.model_validate(symbol)
    kline_data = KlineMessageData.model_validate(kline_data)

    subject = symbol.get_subject()
    records = subject.get(f"_kline_records_{interval.freq}", default=[]) if kline_use_cached_results else []
    if len(records) < kline_limit_size:
        session = _get_session()
        raw = session.get_kline(
            category=symbol.category,
            symbol=symbol.name,
            interval=interval.name,
            limit=kline_limit_size,
        )
        resp = GetKlineAPIResponse.model_validate(raw)
        assert (resp.retMsg == "OK")

        is_fresh_data = True
        action = None

        _records: List[dict] = []
        for result in resp.result.list:
            _records.append({
                'time': result.get_time(),
                'open': result.open,
                'high': result.high,
                'low': result.low,
                'close': result.close,
                'volume': result.volume,
                'turnover': result.turnover,
            })
        records = _records
    else:
        is_fresh_data = False

        ts = pd.to_datetime(kline_data.timestamp).round(freq=interval.freq).isoformat()
        first = records[0]
        if first['time'] == ts:
            action = "updated"
            first['open'] = kline_data.open
            first['high'] = kline_data.high
            first['low'] = kline_data.low
            first['close'] = kline_data.close
            first['volume'] = kline_data.volume
            first['turnover'] = kline_data.turnover
        else:
            action = "new"
            records.insert(0, {
                'time': ts,
                'open': kline_data.open,
                'high': kline_data.high,
                'low': kline_data.low,
                'close': kline_data.close,
                'volume': kline_data.volume,
                'turnover': kline_data.turnover,
            })

        if len(records) > kline_limit_size:
            records = records[:kline_limit_size]

    if kline_use_cached_results or kline_always_cache_results:
        subject.set(f"_kline_records_{interval.freq}", records, muted=True)
        subject.store()

    df = pd.DataFrame.from_records(records)
    df.set_index(pd.DatetimeIndex(pd.to_datetime(df['time'])), inplace=True)
    df.drop('time', axis=1, inplace=True)
    df.sort_index(ascending=True, inplace=True)

    TechnicalAnalysis(df, interval, symbol).run()

    if kline_store_df_on_subject:
        print(">> STORE DF ON SUBJECT")
        buf = io.BytesIO()
        df.to_pickle(buf)
        base64_string = base64.b64encode(buf.getvalue()).decode("utf-8")
        subject.set(f"_kline_dataframe_{interval.freq}", base64_string, muted=True)
        subject.store()
        print("<< DONE")
    else:
        print("!! NOT STORE DF ON SUBJECT")

    return {
        "subject": subject.name,
        "interval": interval.model_dump(),
        "symbol": symbol.model_dump(),
        "is_fresh_data": is_fresh_data,
        "action": action,
    }


def update_instrument_info(symbol: Symbol):

    session: HTTP = _get_session()
    raw = session.get_instruments_info(category=symbol.category, symbol=symbol.name)
    resp = GetInstrumentInfoAPIResponse.model_validate(raw)
    assert (resp.retMsg == "OK")
    assert (len(resp.result.list) == 1)

    subject = symbol.get_subject()
    subject.set("_q", resp.result.list[0].model_dump(), muted=True)
    subject.store()

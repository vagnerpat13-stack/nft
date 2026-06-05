"""Candles históricos via MetaTrader 5 (FBS)."""

from __future__ import annotations

import pandas as pd

from .mt5_session import Mt5Session

TIMEFRAME_MAP = {
    "1m": "TIMEFRAME_M1",
    "5m": "TIMEFRAME_M5",
    "15m": "TIMEFRAME_M15",
    "30m": "TIMEFRAME_M30",
    "1h": "TIMEFRAME_H1",
    "4h": "TIMEFRAME_H4",
    "1d": "TIMEFRAME_D1",
}


def _timeframe(mt5, interval: str):
    key = interval.lower()
    if key not in TIMEFRAME_MAP:
        raise ValueError(f"Intervalo MT5 inválido: {interval}. Use: {list(TIMEFRAME_MAP)}")
    return getattr(mt5, TIMEFRAME_MAP[key])


def _bars_to_df(rates) -> pd.DataFrame:
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time")
    df = df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume",
        }
    )
    return df[["Open", "High", "Low", "Close", "Volume"]]


def fetch_mt5(symbol: str, interval: str, count: int, cfg: dict) -> pd.DataFrame:
    mt5 = Mt5Session.ensure(cfg)
    sym = cfg.get("mt5_symbol", symbol)

    if not mt5.symbol_select(sym, True):
        raise ValueError(f"Símbolo '{sym}' não disponível no MT5. Abra-o no Observação de Mercado.")

    tf = _timeframe(mt5, interval)
    rates = mt5.copy_rates_from_pos(sym, tf, 0, count)
    if rates is None or len(rates) == 0:
        raise ValueError(f"Sem candles para {sym}: {mt5.last_error()}")
    return _bars_to_df(rates)


def fetch_recent_mt5(symbol: str, cfg: dict) -> pd.DataFrame:
    interval = cfg.get("paper_interval", cfg.get("interval", "5m"))
    count = int(cfg.get("mt5_barras", 500))
    return fetch_mt5(symbol, interval, count, cfg)

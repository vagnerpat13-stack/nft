"""Download de dados históricos via yfinance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch(symbol: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"Sem dados para {symbol}. Verifique o símbolo e o período.")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    return df


def fetch_recent(symbol: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
    """Histórico curto para paper trading (indicadores + último candle)."""
    return fetch(symbol, period=period, interval=interval)


def fetch_latest(symbol: str, interval: str = "5m") -> pd.Series:
    df = fetch_recent(symbol, interval=interval, period="5d")
    return df.iloc[-1]

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

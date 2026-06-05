"""Indicadores técnicos para sinais de entrada e saída."""

from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def enrich(df: pd.DataFrame, ema_fast: int, ema_slow: int, rsi_period: int) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out["Close"], ema_fast)
    out["ema_slow"] = ema(out["Close"], ema_slow)
    out["rsi"] = rsi(out["Close"], rsi_period)
    out["atr"] = atr(out["High"], out["Low"], out["Close"])
    out["trend"] = (out["ema_fast"] - out["ema_slow"]) / out["Close"]
    out["volatility"] = out["atr"] / out["Close"]
    return out

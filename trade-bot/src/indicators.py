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


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    line = ema_fast - ema_slow
    sig = ema(line, signal)
    hist = line - sig
    return pd.DataFrame({"macd": line, "macd_signal": sig, "macd_hist": hist})


def bollinger(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    width = (upper - lower) / mid.replace(0, np.nan)
    return pd.DataFrame({"bb_mid": mid, "bb_upper": upper, "bb_lower": lower, "bb_width": width})


def enrich_ema_rsi(
    df: pd.DataFrame, ema_fast: int, ema_slow: int, rsi_period: int
) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out["Close"], ema_fast)
    out["ema_slow"] = ema(out["Close"], ema_slow)
    out["rsi"] = rsi(out["Close"], rsi_period)
    out["atr"] = atr(out["High"], out["Low"], out["Close"])
    out["trend"] = (out["ema_fast"] - out["ema_slow"]) / out["Close"]
    out["volatility"] = out["atr"] / out["Close"]
    return out


def enrich_macd_bb(
    df: pd.DataFrame,
    macd_fast: int,
    macd_slow: int,
    macd_signal: int,
    bb_period: int,
    bb_std: float,
) -> pd.DataFrame:
    out = df.copy()
    macd_df = macd(out["Close"], macd_fast, macd_slow, macd_signal)
    bb_df = bollinger(out["Close"], bb_period, bb_std)
    out = pd.concat([out, macd_df, bb_df], axis=1)
    out["atr"] = atr(out["High"], out["Low"], out["Close"])
    out["trend"] = out["macd_hist"] / out["Close"]
    out["volatility"] = out["atr"] / out["Close"]
    out["rsi"] = rsi(out["Close"], 14)
    return out


# Compatibilidade com código anterior
enrich = enrich_ema_rsi

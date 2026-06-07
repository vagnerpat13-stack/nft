"""EMA rápida — mais cruzamentos, mais operações (sem filtro RSI)."""

from __future__ import annotations

import pandas as pd

from ..indicators import ema, rsi
from ..strategy import Side
from .base import BaseStrategy


class EmaCrossStrategy(BaseStrategy):
    name = "ema_cross"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        fast = int(cfg.get("ema_rapida", 5))
        slow = int(cfg.get("ema_lenta", 13))
        out["ema_fast"] = ema(out["Close"], fast)
        out["ema_slow"] = ema(out["Close"], slow)
        out["rsi"] = rsi(out["Close"], cfg.get("rsi_periodo", 14))
        out["trend"] = (out["ema_fast"] - out["ema_slow"]) / out["Close"]
        out["volatility"] = out["Close"].pct_change().rolling(10).std().fillna(0.02)
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("ema_slow"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        cross_up = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
        cross_down = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]
        if cross_up:
            return "long"
        if cross_down:
            return "short"
        return None

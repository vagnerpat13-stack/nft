"""RSI cruza 50 — operações frequentes na direção do cruzamento."""

from __future__ import annotations

import pandas as pd

from ..indicators import ema, rsi
from ..strategy import Side
from .base import BaseStrategy


class RsiCrossStrategy(BaseStrategy):
    name = "rsi_cross"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        period = cfg.get("rsi_periodo", 14)
        out["rsi"] = rsi(out["Close"], period)
        out["ema_slow"] = ema(out["Close"], cfg.get("ema_filtro", 50))
        out["trend"] = (out["Close"] - out["ema_slow"]) / out["Close"]
        out["volatility"] = out["Close"].pct_change().rolling(14).std().fillna(0.02)
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        level = cfg.get("rsi_nivel", 50)
        if prev["rsi"] <= level < row["rsi"]:
            return "long"
        if prev["rsi"] >= level > row["rsi"]:
            return "short"
        return None

"""Scalp: EMA rápida + RSI confirma direção — muitos sinais, pensado para R:R 1:1,5."""

from __future__ import annotations

import pandas as pd

from ..indicators import ema, rsi
from ..strategy import Side
from .base import BaseStrategy


class ScalpMomentumStrategy(BaseStrategy):
    name = "scalp_momentum"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        out["ema_fast"] = ema(out["Close"], int(cfg.get("ema_rapida", 5)))
        out["ema_slow"] = ema(out["Close"], int(cfg.get("ema_lenta", 13)))
        out["rsi"] = rsi(out["Close"], cfg.get("rsi_periodo", 7))
        out["trend"] = (out["ema_fast"] - out["ema_slow"]) / out["Close"]
        out["volatility"] = out["Close"].pct_change().rolling(8).std().fillna(0.015)
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("ema_slow"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        cross_up = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
        cross_down = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]
        rsi_min_long = cfg.get("scalp_rsi_min_long", 45)
        rsi_max_short = cfg.get("scalp_rsi_max_short", 55)

        if cross_up and row["rsi"] > rsi_min_long:
            return "long"
        if cross_down and row["rsi"] < rsi_max_short:
            return "short"
        return None

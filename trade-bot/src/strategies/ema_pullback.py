"""Pullback na tendência: EMA + RSI — maior taxa de acerto em EURUSD 1h nos testes."""

from __future__ import annotations

import pandas as pd

from ..indicators import enrich_ema_rsi
from ..strategy import Side
from .base import BaseStrategy


class EmaPullbackStrategy(BaseStrategy):
    name = "ema_pullback"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        return enrich_ema_rsi(
            df,
            cfg.get("ema_rapida", 9),
            cfg.get("ema_lenta", 21),
            cfg.get("rsi_periodo", 14),
        )

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        rsi_min_long = cfg.get("pullback_rsi_min_long", 35)
        rsi_max_long = cfg.get("pullback_rsi_max_long", 48)
        rsi_min_short = cfg.get("pullback_rsi_min_short", 52)
        rsi_max_short = cfg.get("pullback_rsi_max_short", 65)

        uptrend = row["ema_fast"] > row["ema_slow"]
        downtrend = row["ema_fast"] < row["ema_slow"]

        if uptrend and rsi_min_long <= row["rsi"] <= rsi_max_long and prev["rsi"] < row["rsi"]:
            return "long"
        if downtrend and rsi_min_short <= row["rsi"] <= rsi_max_short and prev["rsi"] > row["rsi"]:
            return "short"
        return None

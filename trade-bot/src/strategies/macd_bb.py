"""Estratégia: MACD + toque nas Bandas de Bollinger."""

from __future__ import annotations

import pandas as pd

from ..indicators import enrich_macd_bb
from ..strategy import Side
from .base import BaseStrategy


class MacdBbStrategy(BaseStrategy):
    name = "macd_bb"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        return enrich_macd_bb(
            df,
            cfg.get("macd_rapido", 12),
            cfg.get("macd_lento", 26),
            cfg.get("macd_sinal", 9),
            cfg.get("bb_periodo", 20),
            cfg.get("bb_desvio", 2.0),
        )

    def _row_ready(self, row: pd.Series) -> bool:
        needed = ("macd", "macd_signal", "bb_lower", "bb_upper")
        return not any(pd.isna(row.get(c)) for c in needed)

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        macd_cross_up = prev["macd"] <= prev["macd_signal"] and row["macd"] > row["macd_signal"]
        macd_cross_down = prev["macd"] >= prev["macd_signal"] and row["macd"] < row["macd_signal"]

        touch_lower = row["Low"] <= row["bb_lower"] or row["Close"] <= row["bb_lower"]
        touch_upper = row["High"] >= row["bb_upper"] or row["Close"] >= row["bb_upper"]

        if macd_cross_up and touch_lower:
            return "long"
        if macd_cross_down and touch_upper:
            return "short"
        return None

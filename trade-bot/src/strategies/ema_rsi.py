"""Estratégia: cruzamento de EMAs com filtro RSI."""

from __future__ import annotations

import pandas as pd

from ..indicators import enrich_ema_rsi
from ..strategy import Side
from .base import BaseStrategy


class EmaRsiStrategy(BaseStrategy):
    name = "ema_rsi"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        return enrich_ema_rsi(
            df,
            cfg["ema_rapida"],
            cfg["ema_lenta"],
            cfg["rsi_periodo"],
        )

    def _row_ready(self, row: pd.Series) -> bool:
        return not (pd.isna(row.get("rsi")) or pd.isna(row.get("ema_slow")))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        cross_up = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
        cross_down = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]
        rsi_ob = cfg["rsi_sobrecompra"]
        rsi_os = cfg["rsi_sobrevenda"]

        if cross_up and row["rsi"] < rsi_ob:
            return "long"
        if cross_down and row["rsi"] > rsi_os:
            return "short"
        return None

"""Reversão à média nas Bandas de Bollinger."""

from __future__ import annotations

import pandas as pd

from ..indicators import bollinger, rsi
from ..strategy import Side
from .base import BaseStrategy


class BbReversionStrategy(BaseStrategy):
    name = "bb_reversion"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        bb = bollinger(
            out["Close"],
            cfg.get("bb_periodo", 20),
            cfg.get("bb_desvio", 2.0),
        )
        out = pd.concat([out, bb], axis=1)
        out["rsi"] = rsi(out["Close"], cfg.get("rsi_periodo", 14))
        out["trend"] = (out["Close"] - out["bb_mid"]) / out["Close"]
        out["volatility"] = (out["bb_upper"] - out["bb_lower"]) / out["Close"]
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("bb_mid"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        if row["Close"] <= row["bb_lower"] and prev["Close"] > prev["bb_lower"]:
            return "long"
        if row["Close"] >= row["bb_upper"] and prev["Close"] < prev["bb_upper"]:
            return "short"
        return None

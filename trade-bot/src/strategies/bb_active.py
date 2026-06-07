"""Bollinger ativo — entra ao tocar banda (sem exigir cruzamento)."""

from __future__ import annotations

import pandas as pd

from ..indicators import bollinger, rsi
from ..strategy import Side
from .base import BaseStrategy


class BbActiveStrategy(BaseStrategy):
    name = "bb_active"

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
        touch_pct = cfg.get("bb_toque_pct", 0.001)
        lower = row["bb_lower"] * (1 + touch_pct)
        upper = row["bb_upper"] * (1 - touch_pct)

        if row["Low"] <= lower or row["Close"] <= lower:
            return "long"
        if row["High"] >= upper or row["Close"] >= upper:
            return "short"
        return None

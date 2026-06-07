"""RSI extremo + Bollinger — alta seletividade, boa taxa de acerto em testes."""

from __future__ import annotations

import pandas as pd

from ..indicators import bollinger, rsi
from ..strategy import Side
from .base import BaseStrategy


class RsiBbStrategy(BaseStrategy):
    name = "rsi_bb"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        period = cfg.get("bb_periodo", 20)
        std = cfg.get("bb_desvio", 2.0)
        bb = bollinger(out["Close"], period, std)
        out = pd.concat([out, bb], axis=1)
        out["rsi"] = rsi(out["Close"], cfg.get("rsi_periodo", 14))
        out["trend"] = (out["Close"] - out["bb_mid"]) / out["Close"]
        out["volatility"] = (out["bb_upper"] - out["bb_lower"]) / out["Close"]
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi")) and not pd.isna(row.get("bb_lower"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        rsi_os = cfg.get("rsi_sobrevenda", 32)
        rsi_ob = cfg.get("rsi_sobrecompra", 68)
        bb_tol = cfg.get("rsi_bb_tolerancia", 1.005)

        if row["rsi"] < rsi_os and row["Close"] <= row["bb_lower"] * bb_tol:
            return "long"
        if row["rsi"] > rsi_ob and row["Close"] >= row["bb_upper"] / bb_tol:
            return "short"
        return None

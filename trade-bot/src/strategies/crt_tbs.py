"""CRT + TBS — Candle Range Theory + Turtle Body Soup (ICT).

HTF: range do candle de referência (dia ou 4h anterior).
TBS: sweep do extremo + fechamento de volta dentro do range → reversão.
"""

from __future__ import annotations

import pandas as pd

from ..indicators import rsi
from ..strategy import Side
from .base import BaseStrategy


def _reference_range(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    out = df.copy()
    if mode == "4h":
        ref = (
            df.resample("4h")
            .agg({"High": "max", "Low": "min", "Close": "last", "Open": "first"})
            .dropna()
        )
        ref["crt_high"] = ref["High"].shift(1)
        ref["crt_low"] = ref["Low"].shift(1)
        ref["crt_mid"] = (ref["crt_high"] + ref["crt_low"]) / 2
        merged = pd.merge_asof(
            out.sort_index(),
            ref[["crt_high", "crt_low", "crt_mid"]].sort_index(),
            left_index=True,
            right_index=True,
            direction="backward",
        )
        return merged
    # daily (padrão)
    days = df.index.normalize()
    daily = df.groupby(days).agg(d_high=("High", "max"), d_low=("Low", "min"))
    daily["crt_high"] = daily["d_high"].shift(1)
    daily["crt_low"] = daily["d_low"].shift(1)
    daily["crt_mid"] = (daily["crt_high"] + daily["crt_low"]) / 2
    out["_day"] = days
    out = out.join(daily[["crt_high", "crt_low", "crt_mid"]], on="_day")
    out = out.drop(columns=["_day"])
    return out


class CrtTbsStrategy(BaseStrategy):
    name = "crt_tbs"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        mode = cfg.get("crt_referencia", "daily")
        out = _reference_range(df, mode)
        out["rsi"] = rsi(out["Close"], cfg.get("rsi_periodo", 14))
        out["range_width"] = (out["crt_high"] - out["crt_low"]) / out["Close"]
        out["trend"] = (out["Close"] - out["crt_mid"]) / out["Close"]
        out["volatility"] = out["range_width"].fillna(0.02)
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not any(pd.isna(row.get(c)) for c in ("crt_high", "crt_low", "crt_mid"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        hi, lo = float(row["crt_high"]), float(row["crt_low"])
        if hi <= lo:
            return None

        require_body = cfg.get("tbs_exige_corpo", True)
        min_sweep_pct = cfg.get("tbs_sweep_min_pct", 0.0002)

        # TBS LONG: sweep abaixo do CRT low + close de volta acima do low
        swept_low = row["Low"] < lo * (1 - min_sweep_pct)
        back_inside_long = row["Close"] > lo
        if require_body:
            body_trap_long = prev["Close"] < lo or prev["Open"] < lo
        else:
            body_trap_long = prev["Low"] < lo

        if swept_low and back_inside_long and body_trap_long:
            return "long"

        # TBS SHORT: sweep acima do CRT high + close de volta abaixo do high
        swept_high = row["High"] > hi * (1 + min_sweep_pct)
        back_inside_short = row["Close"] < hi
        if require_body:
            body_trap_short = prev["Close"] > hi or prev["Open"] > hi
        else:
            body_trap_short = prev["High"] > hi

        if swept_high and back_inside_short and body_trap_short:
            return "short"

        return None

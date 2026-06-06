"""CRT + TBS — Candle Range Theory + Turtle Body Soup (ICT).

HTF: range do candle de referência (dia ou 4h anterior).
TBS: sweep do extremo + fechamento de volta dentro do range → reversão.
Stop: abaixo/acima do wick do sweep (não % fixo genérico).
Alvo: R:R configurável (padrão 1:1,5) ou extremo oposto do range CRT.
"""

from __future__ import annotations

import pandas as pd

from ..indicators import rsi
from ..strategy import Side, Signal
from ..adaptive import AdaptiveMemory
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
    days = df.index.normalize()
    daily = df.groupby(days).agg(d_high=("High", "max"), d_low=("Low", "min"))
    daily["crt_high"] = daily["d_high"].shift(1)
    daily["crt_low"] = daily["d_low"].shift(1)
    daily["crt_mid"] = (daily["crt_high"] + daily["crt_low"]) / 2
    out["_day"] = days
    out = out.join(daily[["crt_high", "crt_low", "crt_mid"]], on="_day")
    return out.drop(columns=["_day"])


def _exit_levels(side: Side, row: pd.Series, cfg: dict) -> tuple[float, float] | None:
    """Stop além do sweep + alvo R:R 1:1,5 (ou extremo CRT se mais próximo)."""
    hi = float(row["crt_high"])
    lo = float(row["crt_low"])
    entry = float(row["Close"])
    buffer = float(cfg.get("crt_stop_buffer_pct", 0.0005))
    rr = float(cfg.get("rr_ratio", 1.5))
    max_stop_pct = float(cfg.get("crt_stop_max_pct", 0.015))
    use_opposite = cfg.get("crt_alvo_extremo", True)

    if side == "long":
        sweep = float(row["Low"])
        stop = sweep * (1 - buffer)
        if stop >= entry:
            return None
        risk = entry - stop
        if risk / entry > max_stop_pct:
            stop = entry * (1 - max_stop_pct)
            risk = entry - stop
        target_rr = entry + risk * rr
        target = min(target_rr, hi) if use_opposite else target_rr
        if target <= entry:
            target = target_rr
    else:
        sweep = float(row["High"])
        stop = sweep * (1 + buffer)
        if stop <= entry:
            return None
        risk = stop - entry
        if risk / entry > max_stop_pct:
            stop = entry * (1 + max_stop_pct)
            risk = stop - entry
        target_rr = entry - risk * rr
        target = max(target_rr, lo) if use_opposite else target_rr
        if target >= entry:
            target = target_rr

    return stop, target


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

        swept_low = row["Low"] < lo * (1 - min_sweep_pct)
        back_inside_long = row["Close"] > lo
        body_trap_long = (
            (prev["Close"] < lo or prev["Open"] < lo)
            if require_body
            else prev["Low"] < lo
        )
        if swept_low and back_inside_long and body_trap_long:
            return "long"

        swept_high = row["High"] > hi * (1 + min_sweep_pct)
        back_inside_short = row["Close"] < hi
        body_trap_short = (
            (prev["Close"] > hi or prev["Open"] > hi)
            if require_body
            else prev["High"] > hi
        )
        if swept_high and back_inside_short and body_trap_short:
            return "short"
        return None

    def signal_at_bar(
        self,
        enriched: pd.DataFrame,
        i: int,
        memory: AdaptiveMemory,
        cfg: dict,
    ) -> Signal | None:
        if i < 1:
            return None
        row, prev = enriched.iloc[i], enriched.iloc[i - 1]
        if not self._row_ready(row):
            return None

        side = self.raw_signal(row, prev, cfg)
        if side is None:
            return None

        ctx = self.context_from_row(row, side)
        if not memory.aceita(ctx):
            return None

        levels = _exit_levels(side, row, cfg)
        if levels is None:
            return None
        stop, target = levels

        return Signal(
            index=i,
            side=side,
            price=float(row["Close"]),
            confianca=memory.confianca(ctx),
            context=ctx,
            stop_price=stop,
            target_price=target,
        )

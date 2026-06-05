"""Geração de sinais com filtro adaptativo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from .adaptive import AdaptiveMemory, SignalContext

Side = Literal["long", "short"]


@dataclass
class Signal:
    index: int
    side: Side
    price: float
    confianca: float
    context: SignalContext


def raw_signal(row: pd.Series, prev: pd.Series, rsi_ob: float, rsi_os: float) -> Side | None:
    cross_up = prev["ema_fast"] <= prev["ema_slow"] and row["ema_fast"] > row["ema_slow"]
    cross_down = prev["ema_fast"] >= prev["ema_slow"] and row["ema_fast"] < row["ema_slow"]

    if cross_up and row["rsi"] < rsi_ob:
        return "long"
    if cross_down and row["rsi"] > rsi_os:
        return "short"
    return None


def generate_signals(
    df: pd.DataFrame,
    memory: AdaptiveMemory,
    rsi_ob: float,
    rsi_os: float,
) -> list[Signal]:
    signals: list[Signal] = []
    for i in range(1, len(df)):
        row, prev = df.iloc[i], df.iloc[i - 1]
        if pd.isna(row["rsi"]) or pd.isna(row["ema_slow"]):
            continue

        side = raw_signal(row, prev, rsi_ob, rsi_os)
        if side is None:
            continue

        ctx = SignalContext(
            side=side,
            trend=float(row["trend"]),
            rsi=float(row["rsi"]),
            volatility=float(row["volatility"]),
        )
        if not memory.aceita(ctx):
            continue

        signals.append(
            Signal(
                index=i,
                side=side,
                price=float(row["Close"]),
                confianca=memory.confianca(ctx),
                context=ctx,
            )
        )
    return signals

"""Interface comum para estratégias."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pandas as pd

from ..adaptive import AdaptiveMemory, SignalContext
from ..strategy import Signal, Side

if TYPE_CHECKING:
    pass


class BaseStrategy(ABC):
    name: str = "base"

    @abstractmethod
    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        ...

    @abstractmethod
    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        ...

    def context_from_row(self, row: pd.Series, side: Side) -> SignalContext:
        return SignalContext(
            side=side,
            trend=float(row.get("trend", 0) or 0),
            rsi=float(row.get("rsi", 50) or 50),
            volatility=float(row.get("volatility", 0.02) or 0.02),
        )

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

        return Signal(
            index=i,
            side=side,
            price=float(row["Close"]),
            confianca=memory.confianca(ctx),
            context=ctx,
        )

    @abstractmethod
    def _row_ready(self, row: pd.Series) -> bool:
        ...

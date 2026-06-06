"""Tipos compartilhados de sinais."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .adaptive import SignalContext

Side = Literal["long", "short"]


@dataclass
class Signal:
    index: int
    side: Side
    price: float
    confianca: float
    context: SignalContext
    stop_price: float | None = None
    target_price: float | None = None

"""Registro de estratégias disponíveis."""

from __future__ import annotations

from .base import BaseStrategy
from .ema_rsi import EmaRsiStrategy
from .macd_bb import MacdBbStrategy

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "ema_rsi": EmaRsiStrategy,
    "macd_bb": MacdBbStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    key = name.lower().strip()
    if key not in STRATEGIES:
        opcoes = ", ".join(STRATEGIES)
        raise ValueError(f"Estratégia '{name}' inválida. Opções: {opcoes}")
    return STRATEGIES[key]()

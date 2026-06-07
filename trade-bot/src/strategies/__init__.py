"""Registro de estratégias disponíveis."""

from __future__ import annotations

from .base import BaseStrategy
from .bb_active import BbActiveStrategy
from .bb_reversion import BbReversionStrategy
from .crt_tbs import CrtTbsStrategy
from .ema_cross import EmaCrossStrategy
from .ema_pullback import EmaPullbackStrategy
from .ema_rsi import EmaRsiStrategy
from .macd_bb import MacdBbStrategy
from .rsi_bb import RsiBbStrategy
from .rsi_cross import RsiCrossStrategy
from .scalp_momentum import ScalpMomentumStrategy

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "ema_rsi": EmaRsiStrategy,
    "macd_bb": MacdBbStrategy,
    "rsi_bb": RsiBbStrategy,
    "ema_pullback": EmaPullbackStrategy,
    "bb_reversion": BbReversionStrategy,
    "ema_cross": EmaCrossStrategy,
    "bb_active": BbActiveStrategy,
    "rsi_cross": RsiCrossStrategy,
    "scalp_momentum": ScalpMomentumStrategy,
    "crt_tbs": CrtTbsStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    key = name.lower().strip()
    if key not in STRATEGIES:
        opcoes = ", ".join(STRATEGIES)
        raise ValueError(f"Estratégia '{name}' inválida. Opções: {opcoes}")
    return STRATEGIES[key]()

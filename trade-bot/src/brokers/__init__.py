"""Corretoras: simulada, Alpaca (EUA) e MetaTrader 5 (FBS)."""

from __future__ import annotations

from .base import BaseBroker, OrderResult, Quote
from .simulated import SimulatedBroker

__all__ = ["BaseBroker", "OrderResult", "Quote", "SimulatedBroker", "get_broker"]


def get_broker(name: str, cfg: dict) -> BaseBroker:
    key = name.lower().strip()
    if key in ("simulado", "simulated", "paper"):
        return SimulatedBroker(cfg)
    if key == "alpaca":
        from .alpaca import AlpacaBroker

        return AlpacaBroker(cfg)
    if key in ("mt5", "fbs", "metatrader", "metatrader5"):
        from .mt5_broker import Mt5Broker

        return Mt5Broker(cfg)
    raise ValueError(
        f"Broker '{name}' inválido. Use: simulado, alpaca, mt5 (FBS/MetaTrader 5)"
    )

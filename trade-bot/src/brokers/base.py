"""Interface de corretora."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Side = Literal["long", "short"]


@dataclass
class Quote:
    symbol: str
    price: float
    high: float
    low: float
    timestamp: str


@dataclass
class OrderResult:
    ok: bool
    order_id: str
    filled_price: float
    quantity: float
    message: str = ""


class BaseBroker(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        ...

    @abstractmethod
    def get_cash(self) -> float:
        ...

    def submit_market(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        stop: float | None = None,
        target: float | None = None,
    ) -> OrderResult:
        ...

    @abstractmethod
    def close_position(self, symbol: str) -> OrderResult | None:
        ...

    def sync_capital(self, engine_capital: float) -> None:
        """Opcional: alinha capital do engine com a corretora."""

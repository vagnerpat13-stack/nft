"""Corretora simulada — usa yfinance para cotações."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..data import fetch_latest
from .base import BaseBroker, OrderResult, Quote, Side


@dataclass
class SimulatedBroker(BaseBroker):
    cfg: dict
    cash: float = 0.0
    positions: dict[str, dict] = field(default_factory=dict)
    order_seq: int = 0

    def __post_init__(self) -> None:
        if self.cash <= 0:
            self.cash = float(self.cfg.get("capital_inicial", 10000))

    def get_quote(self, symbol: str) -> Quote:
        bar = fetch_latest(symbol, interval=self.cfg.get("interval", "5m"))
        ts = str(bar.name)
        return Quote(
            symbol=symbol,
            price=float(bar["Close"]),
            high=float(bar["High"]),
            low=float(bar["Low"]),
            timestamp=ts,
        )

    def get_cash(self) -> float:
        return self.cash

    def submit_market(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        stop: float | None = None,
        target: float | None = None,
    ) -> OrderResult:
        quote = self.get_quote(symbol)
        cost = quote.price * quantity
        self.order_seq += 1
        oid = f"SIM-{self.order_seq}"

        if side == "long":
            if cost > self.cash:
                return OrderResult(False, oid, 0, 0, "Saldo insuficiente")
            self.cash -= cost
            self.positions[symbol] = {"side": "long", "qty": quantity, "entry": quote.price}
        else:
            self.positions[symbol] = {"side": "short", "qty": quantity, "entry": quote.price}

        return OrderResult(True, oid, quote.price, quantity, "paper simulado")

    def close_position(self, symbol: str) -> OrderResult | None:
        pos = self.positions.get(symbol)
        if not pos:
            return None
        quote = self.get_quote(symbol)
        qty = pos["qty"]
        entry = pos["entry"]
        if pos["side"] == "long":
            pnl_val = (quote.price - entry) * qty
            self.cash += quote.price * qty
        else:
            pnl_val = (entry - quote.price) * qty
            self.cash += pnl_val + entry * qty
        del self.positions[symbol]
        self.order_seq += 1
        return OrderResult(
            True,
            f"SIM-CLOSE-{self.order_seq}",
            quote.price,
            qty,
            f"fechado pnl~{pnl_val:.2f}",
        )

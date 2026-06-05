"""Gestão de risco e dimensionamento de posição."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskConfig:
    capital: float
    risco_por_operacao: float
    stop_loss_pct: float
    take_profit_pct: float
    max_operacoes_dia: int
    drawdown_max_pct: float


@dataclass
class Position:
    side: str
    entry_price: float
    quantity: float
    stop: float
    target: float
    entry_index: int
    confianca_entrada: float
    context: object  # SignalContext — evita import circular


def apply_rr_ratio(cfg: dict) -> dict:
    """
    Garante take_profit = stop × rr_ratio quando rr_ratio está definido.
    Ex.: rr_ratio: 1.5 → risco 1, alvo 1,5 (sempre 1:1,5).
    """
    ratio = cfg.get("rr_ratio")
    if ratio is None:
        return cfg
    sl = float(cfg.get("stop_loss_pct", 0.01))
    cfg = {**cfg, "take_profit_pct": round(sl * float(ratio), 6)}
    return cfg


def position_size(capital: float, entry: float, stop_pct: float, risk_pct: float) -> float:
    risk_amount = capital * risk_pct
    stop_distance = entry * stop_pct
    if stop_distance <= 0:
        return 0.0
    qty = risk_amount / stop_distance
    max_qty = (capital * 0.95) / entry
    return max(0.0, min(qty, max_qty))


def open_position(
    side: str,
    price: float,
    index: int,
    cfg: RiskConfig,
    context: object,
    confianca: float,
) -> Position | None:
    qty = position_size(cfg.capital, price, cfg.stop_loss_pct, cfg.risco_por_operacao)
    if qty <= 0:
        return None

    if side == "long":
        stop = price * (1 - cfg.stop_loss_pct)
        target = price * (1 + cfg.take_profit_pct)
    else:
        stop = price * (1 + cfg.stop_loss_pct)
        target = price * (1 - cfg.take_profit_pct)

    return Position(
        side=side,
        entry_price=price,
        quantity=qty,
        stop=stop,
        target=target,
        entry_index=index,
        confianca_entrada=confianca,
        context=context,
    )


def check_exit(pos: Position, high: float, low: float, close: float) -> tuple[float, str] | None:
    """Retorna (preço saída, motivo) se stop/target/intraday atingido."""
    if pos.side == "long":
        if low <= pos.stop:
            return pos.stop, "stop"
        if high >= pos.target:
            return pos.target, "target"
    else:
        if high >= pos.stop:
            return pos.stop, "stop"
        if low <= pos.target:
            return pos.target, "target"
    return None


def pnl(pos: Position, exit_price: float) -> float:
    if pos.side == "long":
        return (exit_price - pos.entry_price) * pos.quantity
    return (pos.entry_price - exit_price) * pos.quantity

"""Motor de backtest com adaptação contínua aos erros."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .engine import EngineState, TradeRecord, TradingEngine
from .risk import apply_rr_ratio
from .strategies import get_strategy


@dataclass
class BacktestResult:
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    capital_final: float = 0.0
    taxa_acerto: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    total_operacoes: int = 0
    memoria: dict = field(default_factory=dict)
    halted: bool = False


def run_backtest(df: pd.DataFrame, cfg: dict) -> BacktestResult:
    cfg = apply_rr_ratio(cfg)
    strategy = get_strategy(cfg.get("estrategia", "ema_rsi"))
    enriched = strategy.enrich(df, cfg)
    engine = TradingEngine(strategy, cfg)
    engine.run_series(enriched)

    metrics = engine.metrics()
    equity = [cfg["capital_inicial"]]
    running = cfg["capital_inicial"]
    for t in engine.state.trades:
        running += t.lucro
        equity.append(running)

    return BacktestResult(
        trades=engine.state.trades,
        equity_curve=equity,
        capital_final=metrics["capital_final"],
        taxa_acerto=metrics["taxa_acerto"],
        profit_factor=metrics["profit_factor"],
        max_drawdown_pct=metrics["max_drawdown_pct"],
        total_operacoes=metrics["total_operacoes"],
        memoria=metrics["memoria"],
        halted=metrics["halted"],
    )

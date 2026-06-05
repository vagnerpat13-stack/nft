"""Motor de trading compartilhado (backtest e paper)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .adaptive import AdaptiveMemory
from .risk import Position, RiskConfig, check_exit, open_position, pnl
from .strategies.base import BaseStrategy
from .strategy import Signal


@dataclass
class TradeRecord:
    entrada: str
    saida: str
    lado: str
    preco_entrada: float
    preco_saida: float
    lucro: float
    motivo: str
    confianca: float


@dataclass
class EngineState:
    capital: float
    peak: float
    position: Position | None = None
    ops_no_dia: dict[str, int] = field(default_factory=dict)
    trades: list[TradeRecord] = field(default_factory=list)
    halted: bool = False


@dataclass
class StepResult:
    trade_closed: TradeRecord | None = None
    position_opened: bool = False
    halted: bool = False


class TradingEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        cfg: dict,
        memory: AdaptiveMemory | None = None,
        state: EngineState | None = None,
    ):
        self.strategy = strategy
        self.cfg = cfg
        self.memory = memory or AdaptiveMemory(
            penalidade_erro=cfg["penalidade_erro"],
            bonus_acerto=cfg["bonus_acerto"],
            decaimento=cfg["decaimento_memoria"],
            confianca_minima=cfg["confianca_minima"],
        )
        self.risk = RiskConfig(
            capital=cfg["capital_inicial"],
            risco_por_operacao=cfg["risco_por_operacao"],
            stop_loss_pct=cfg["stop_loss_pct"],
            take_profit_pct=cfg["take_profit_pct"],
            max_operacoes_dia=cfg["max_operacoes_dia"],
            drawdown_max_pct=cfg["drawdown_max_pct"],
        )
        self.state = state or EngineState(
            capital=cfg["capital_inicial"],
            peak=cfg["capital_inicial"],
        )
        self._sync_risk_capital()

    def _sync_risk_capital(self) -> None:
        self.risk.capital = self.state.capital

    def step(self, enriched: pd.DataFrame, i: int, force_close_last: bool = False) -> StepResult:
        if self.state.halted:
            return StepResult(halted=True)

        row = enriched.iloc[i]
        date_key = str(row.name)[:10]
        closed: TradeRecord | None = None
        opened = False

        if self.state.peak > 0 and self.state.capital <= self.state.peak * (
            1 - self.risk.drawdown_max_pct
        ):
            self.state.halted = True
            return StepResult(halted=True)

        if self.state.position is not None:
            exit_info = check_exit(
                self.state.position,
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
            )
            if exit_info is None and force_close_last:
                exit_info = (float(row["Close"]), "fechamento")

            if exit_info:
                exit_price, motivo = exit_info
                lucro = pnl(self.state.position, exit_price)
                self.state.capital += lucro
                self.memory.registrar(self.state.position.context, lucro)
                closed = TradeRecord(
                    entrada=str(enriched.index[self.state.position.entry_index]),
                    saida=str(row.name),
                    lado=self.state.position.side,
                    preco_entrada=self.state.position.entry_price,
                    preco_saida=exit_price,
                    lucro=round(lucro, 2),
                    motivo=motivo,
                    confianca=self.state.position.confianca_entrada,
                )
                self.state.trades.append(closed)
                self.state.position = None
                self._sync_risk_capital()

        if self.state.position is None and not self.state.halted:
            sig = self.strategy.signal_at_bar(enriched, i, self.memory, self.cfg)
            if sig and self.state.ops_no_dia.get(date_key, 0) < self.risk.max_operacoes_dia:
                pos = open_position(
                    sig.side,
                    sig.price,
                    i,
                    self.risk,
                    sig.context,
                    sig.confianca,
                )
                if pos:
                    self.state.position = pos
                    self.state.ops_no_dia[date_key] = self.state.ops_no_dia.get(date_key, 0) + 1
                    opened = True

        self.state.peak = max(self.state.peak, self.state.capital)
        return StepResult(trade_closed=closed, position_opened=opened, halted=self.state.halted)

    def run_series(self, enriched: pd.DataFrame) -> EngineState:
        for i in range(len(enriched)):
            self.step(enriched, i, force_close_last=(i == len(enriched) - 1))
        return self.state

    def metrics(self) -> dict:
        trades = self.state.trades
        wins = [t for t in trades if t.lucro > 0]
        losses = [t for t in trades if t.lucro < 0]
        gross_win = sum(t.lucro for t in wins) or 0.01
        gross_loss = abs(sum(t.lucro for t in losses)) or 0.01
        max_dd = 0.0
        peak = self.cfg["capital_inicial"]
        equity = self.cfg["capital_inicial"]
        for t in trades:
            equity += t.lucro
            peak = max(peak, equity)
            if peak > 0:
                max_dd = max(max_dd, (peak - equity) / peak)

        return {
            "capital_final": round(self.state.capital, 2),
            "taxa_acerto": round(len(wins) / len(trades) * 100, 2) if trades else 0.0,
            "profit_factor": round(gross_win / gross_loss, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "total_operacoes": len(trades),
            "memoria": self.memory.resumo(),
            "halted": self.state.halted,
        }

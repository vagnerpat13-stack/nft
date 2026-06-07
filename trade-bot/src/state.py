"""Persistência de estado para paper trading."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .adaptive import AdaptiveMemory
from .engine import EngineState, TradingEngine
from .risk import Position


def _key_to_str(key: tuple) -> str:
    return "|".join(str(x) for x in key)


def _key_from_str(s: str) -> tuple:
    parts = s.split("|")
    return (int(parts[0]), int(parts[1]), int(parts[2]), parts[3])


@dataclass
class PersistedState:
    symbol: str
    estrategia: str
    capital: float
    peak: float
    halted: bool
    last_bar_ts: str | None
    ops_no_dia: dict[str, int]
    memory_scores: dict[str, float]
    position: dict[str, Any] | None
    trades: list[dict[str, Any]]

    @classmethod
    def from_engine(
        cls,
        engine: TradingEngine,
        symbol: str,
        estrategia: str,
        last_bar_ts: str | None,
    ) -> PersistedState:
        pos_dict = None
        if engine.state.position:
            p = engine.state.position
            pos_dict = {
                "side": p.side,
                "entry_price": p.entry_price,
                "quantity": p.quantity,
                "stop": p.stop,
                "target": p.target,
                "entry_index": p.entry_index,
                "confianca_entrada": p.confianca_entrada,
                "context": {
                    "side": p.context.side,
                    "trend": p.context.trend,
                    "rsi": p.context.rsi,
                    "volatility": p.context.volatility,
                },
            }
        scores = {_key_to_str(k): v for k, v in engine.memory.scores.items()}
        trades = [asdict(t) for t in engine.state.trades]
        return cls(
            symbol=symbol,
            estrategia=estrategia,
            capital=engine.state.capital,
            peak=engine.state.peak,
            halted=engine.state.halted,
            last_bar_ts=last_bar_ts,
            ops_no_dia=dict(engine.state.ops_no_dia),
            memory_scores=scores,
            position=pos_dict,
            trades=trades,
        )

    def apply_to_engine(self, engine: TradingEngine, cfg: dict) -> None:
        engine.state.capital = self.capital
        engine.state.peak = self.peak
        engine.state.halted = self.halted
        engine.state.ops_no_dia = dict(self.ops_no_dia)
        engine.memory.scores = {_key_from_str(k): v for k, v in self.memory_scores.items()}
        engine._sync_risk_capital()

        if self.position:
            from .adaptive import SignalContext

            ctx_data = self.position["context"]
            ctx = SignalContext(
                side=ctx_data["side"],
                trend=ctx_data["trend"],
                rsi=ctx_data["rsi"],
                volatility=ctx_data["volatility"],
            )
            engine.state.position = Position(
                side=self.position["side"],
                entry_price=self.position["entry_price"],
                quantity=self.position["quantity"],
                stop=self.position["stop"],
                target=self.position["target"],
                entry_index=self.position["entry_index"],
                confianca_entrada=self.position["confianca_entrada"],
                context=ctx,
            )

        from .engine import TradeRecord

        engine.state.trades = [TradeRecord(**t) for t in self.trades]


def load_state(path: Path) -> PersistedState | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return PersistedState(**data)


def save_state(path: Path, state: PersistedState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")

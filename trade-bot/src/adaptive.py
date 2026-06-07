"""Memória adaptativa: ajusta confiança conforme acertos e erros."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Side = Literal["long", "short"]


def _bucket(value: float, edges: tuple[float, ...]) -> int:
    for i, edge in enumerate(edges):
        if value < edge:
            return i
    return len(edges)


@dataclass
class SignalContext:
    """Contexto do sinal para aprendizado pós-operacao."""

    side: Side
    trend: float
    rsi: float
    volatility: float

    def key(self) -> tuple[int, int, int, Side]:
        trend_b = _bucket(self.trend, (-0.02, -0.005, 0.005, 0.02))
        rsi_b = _bucket(self.rsi, (35, 45, 55, 65))
        vol_b = _bucket(self.volatility, (0.01, 0.02, 0.035, 0.05))
        return (trend_b, rsi_b, vol_b, self.side)


@dataclass
class AdaptiveMemory:
    """Pontua cada 'regime' de mercado; penaliza padrões que geraram perdas."""

    penalidade_erro: float = 0.12
    bonus_acerto: float = 0.04
    decaimento: float = 0.995
    confianca_minima: float = 0.45
    scores: dict[tuple, float] = field(default_factory=dict)

    def confianca(self, ctx: SignalContext) -> float:
        base = 0.55
        score = self.scores.get(ctx.key(), 0.0)
        return max(0.0, min(1.0, base + score))

    def aceita(self, ctx: SignalContext) -> bool:
        return self.confianca(ctx) >= self.confianca_minima

    def registrar(self, ctx: SignalContext, lucro: float) -> None:
        key = ctx.key()
        atual = self.scores.get(key, 0.0) * self.decaimento
        if lucro > 0:
            self.scores[key] = atual + self.bonus_acerto
        elif lucro < 0:
            self.scores[key] = atual - self.penalidade_erro
        else:
            self.scores[key] = atual

    def resumo(self) -> dict:
        if not self.scores:
            return {"regimes": 0, "media_score": 0.0}
        vals = list(self.scores.values())
        return {
            "regimes": len(self.scores),
            "media_score": round(sum(vals) / len(vals), 4),
            "bloqueados": sum(
                1 for k in self.scores if 0.55 + self.scores[k] < self.confianca_minima
            ),
        }

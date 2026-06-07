#!/usr/bin/env python3
"""Forex: melhor taxa de acerto com R:R stop 1 : alvo 3."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import fetch
from src.engine import TradingEngine
from src.strategies import STRATEGIES
from src.strategies.base import BaseStrategy


@dataclass
class Row:
    nome: str
    symbol: str
    tf: str
    sl: float
    ops: int
    winrate: float
    retorno: float
    pf: float
    expectancy: float


def run(
    strat: BaseStrategy,
    df,
    cfg: dict,
    sl_pct: float,
    symbol: str,
    tf: str,
) -> Row:
    tp_pct = sl_pct * 3  # 1:3
    c = {
        **cfg,
        "stop_loss_pct": sl_pct,
        "take_profit_pct": tp_pct,
        "confianca_minima": 0.45,
    }
    enriched = strat.enrich(df, c)
    engine = TradingEngine(strat, c)
    engine.run_series(enriched)
    m = engine.metrics()
    trades = engine.state.trades
    ret = (m["capital_final"] / cfg["capital_inicial"] - 1) * 100
    if trades:
        exp = sum(t.lucro for t in trades) / len(trades)
    else:
        exp = 0.0
    return Row(
        strat.name,
        symbol,
        tf,
        sl_pct,
        m["total_operacoes"],
        m["taxa_acerto"],
        ret,
        m["profit_factor"],
        exp,
    )


def main() -> None:
    base = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    base["capital_inicial"] = 10000.0
    base["risco_por_operacao"] = 0.01
    base["max_operacoes_dia"] = 5

    pairs = [
        ("EURUSD=X", "1h", "730d"),
        ("EURUSD=X", "4h", "730d"),
        ("GBPUSD=X", "1h", "730d"),
        ("USDJPY=X", "1h", "730d"),
        ("EURUSD=X", "1d", "2y"),
    ]
    sl_levels = [0.005, 0.008, 0.01, 0.012, 0.015]

    rows: list[Row] = []
    for symbol, tf, period in pairs:
        try:
            df = fetch(symbol, period=period, interval=tf)
        except Exception as e:
            print(f"skip {symbol} {tf}: {e}")
            continue
        for name, cls in STRATEGIES.items():
            strat = cls()
            for sl in sl_levels:
                r = run(strat, df, base, sl, symbol, tf)
                if r.ops >= 8:
                    rows.append(r)

    # Viável: winrate alta + retorno positivo ou PF > 1
    rows.sort(key=lambda x: (-x.winrate, -x.pf, -x.retorno))

    print("\n=== TOP 20 — maior taxa de acerto (R:R 1:3, mín. 8 ops) ===\n")
    print(
        f"{'#':<3} {'Estratégia':<14} {'Par':<10} {'TF':<4} "
        f"{'SL%':>5} {'TP%':>5} {'Ops':>4} {'Acerto':>7} {'Ret%':>8} {'PF':>5}"
    )
    print("-" * 78)
    for i, r in enumerate(rows[:20], 1):
        tp = r.sl * 3 * 100
        print(
            f"{i:<3} {r.nome:<14} {r.symbol:<10} {r.tf:<4} "
            f"{r.sl*100:>4.1f} {tp:>4.1f} {r.ops:>4} {r.winrate:>6.1f}% "
            f"{r.retorno:>+7.2f}% {r.pf:>5.2f}"
        )

  # Mínimo 25% acerto para 1:3 ser matematicamente break-even sem adaptação
    viable = [r for r in rows if r.winrate >= 28 and r.ops >= 8]
    viable.sort(key=lambda x: (-x.winrate, -x.retorno))
    print("\n=== Melhores com acerto >= 28% (break-even teórico ~25% no 1:3) ===\n")
    for r in viable[:10]:
        print(
            f"  {r.nome} | {r.symbol} {r.tf} | SL {r.sl*100:.1f}% TP {r.sl*3*100:.1f}% | "
            f"acerto {r.winrate:.1f}% | ret {r.retorno:+.2f}% | ops {r.ops} | PF {r.pf:.2f}"
        )

    profit = [r for r in rows if r.retorno > 0 and r.ops >= 8]
    profit.sort(key=lambda x: (-x.winrate, -x.retorno))
    print("\n=== Lucrativas no backtest (retorno > 0) ===\n")
    if not profit:
        print("  Nenhuma com retorno positivo neste universo.")
    else:
        for r in profit[:8]:
            print(
                f"  {r.nome} | {r.symbol} {r.tf} | acerto {r.winrate:.1f}% | "
                f"ret {r.retorno:+.2f}% | SL/TP {r.sl*100:.1f}%/{r.sl*3*100:.1f}%"
            )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Executa backtest do robô adaptativo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.backtest import run_backtest  # noqa: E402
from src.data import fetch  # noqa: E402


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_report(result, symbol: str, capital_inicial: float) -> None:
    retorno = (result.capital_final / capital_inicial - 1) * 100
    print(f"\n{'=' * 50}")
    print(f"  Backtest — {symbol}")
    print(f"{'=' * 50}")
    print(f"  Capital inicial:     R$ {capital_inicial:,.2f}")
    print(f"  Capital final:       R$ {result.capital_final:,.2f}")
    print(f"  Retorno:             {retorno:+.2f}%")
    print(f"  Operações:           {result.total_operacoes}")
    print(f"  Taxa de acerto:      {result.taxa_acerto}%")
    print(f"  Profit factor:       {result.profit_factor}")
    print(f"  Max drawdown:        {result.max_drawdown_pct}%")
    print(f"  Regimes na memória:  {result.memoria}")
    print(f"{'=' * 50}\n")

    if result.trades:
        print("Últimas 5 operações:")
        for t in result.trades[-5:]:
            sinal = "+" if t.lucro > 0 else ""
            print(
                f"  {t.lado:5} {t.entrada[:10]} → {t.saida[:10]} | "
                f"{sinal}R$ {t.lucro:.2f} ({t.motivo}) conf={t.confianca:.2f}"
            )
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Robô de trade adaptativo")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=ROOT / "config.yaml",
        help="Arquivo de configuração",
    )
    parser.add_argument("--symbol", help="Sobrescreve símbolo do config")
    parser.add_argument("--period", help="Sobrescreve período (ex: 1y, 2y)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    symbol = args.symbol or cfg["symbol"]
    period = args.period or cfg.get("period", "2y")

    print(f"Baixando dados: {symbol} ({period})...")
    df = fetch(symbol, period=period, interval=cfg.get("interval", "1d"))
    print(f"Candles: {len(df)}")

    result = run_backtest(df, cfg)
    print_report(result, symbol, cfg["capital_inicial"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

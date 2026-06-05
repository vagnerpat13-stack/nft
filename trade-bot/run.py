#!/usr/bin/env python3
"""CLI: backtest e paper trading do robô adaptativo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.backtest import run_backtest  # noqa: E402
from src.data import fetch  # noqa: E402
from src.paper_trading import run_paper_loop  # noqa: E402


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_report(result, symbol: str, capital_inicial: float, estrategia: str) -> None:
    retorno = (result.capital_final / capital_inicial - 1) * 100
    print(f"\n{'=' * 50}")
    print(f"  Backtest — {symbol} ({estrategia})")
    print(f"{'=' * 50}")
    print(f"  Capital inicial:     R$ {capital_inicial:,.2f}")
    print(f"  Capital final:       R$ {result.capital_final:,.2f}")
    print(f"  Retorno:             {retorno:+.2f}%")
    print(f"  Operações:           {result.total_operacoes}")
    print(f"  Taxa de acerto:      {result.taxa_acerto}%")
    print(f"  Profit factor:       {result.profit_factor}")
    print(f"  Max drawdown:        {result.max_drawdown_pct}%")
    print(f"  Parado por drawdown: {'sim' if result.halted else 'não'}")
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


def cmd_backtest(cfg: dict, args: argparse.Namespace) -> int:
    symbol = args.symbol or cfg["symbol"]
    period = args.period or cfg.get("period", "2y")
    estrategia = args.estrategia or cfg.get("estrategia", "ema_rsi")
    cfg = {**cfg, "estrategia": estrategia}

    print(f"Backtest | {symbol} | {estrategia} | {period}")
    df = fetch(symbol, period=period, interval=cfg.get("interval", "1d"))
    print(f"Candles: {len(df)}")

    result = run_backtest(df, cfg)
    print_report(result, symbol, cfg["capital_inicial"], estrategia)
    return 0


def cmd_paper(cfg: dict, args: argparse.Namespace) -> int:
    symbol = args.symbol or cfg["symbol"]
    if args.estrategia:
        cfg = {**cfg, "estrategia": args.estrategia}
    run_paper_loop(cfg, symbol, once=args.once)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Robô de trade adaptativo")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=ROOT / "config.yaml",
        help="Arquivo de configuração",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_bt = sub.add_parser("backtest", help="Simulação histórica")
    p_bt.add_argument("--symbol", help="Símbolo (ex: PETR4.SA, AAPL)")
    p_bt.add_argument("--period", help="Período yfinance (1y, 2y)")
    p_bt.add_argument(
        "--estrategia",
        choices=["ema_rsi", "macd_bb"],
        help="ema_rsi ou macd_bb",
    )

    p_paper = sub.add_parser("paper", help="Paper trading em tempo real")
    p_paper.add_argument("--symbol", help="Símbolo")
    p_paper.add_argument("--estrategia", choices=["ema_rsi", "macd_bb"])
    p_paper.add_argument(
        "--once",
        action="store_true",
        help="Executa um único ciclo (útil para teste)",
    )

    args = parser.parse_args()
    cfg = load_config(args.config)

    if args.command == "backtest":
        return cmd_backtest(cfg, args)
    if args.command == "paper":
        return cmd_paper(cfg, args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

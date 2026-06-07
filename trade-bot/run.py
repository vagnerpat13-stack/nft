#!/usr/bin/env python3
"""CLI: backtest e paper trading do robô adaptativo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.backtest import run_backtest  # noqa: E402
from src.data import fetch  # noqa: E402
from src.paper_trading import run_paper_loop  # noqa: E402


def load_config(path: Path) -> dict:
    from src.risk import apply_rr_ratio

    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return apply_rr_ratio(cfg)


MOTIVO_LABEL = {
    "be": "breakeven (proteger lucro)",
    "trail": "trailing (proteger lucro)",
    "apertar": "apertar (reduzir perda — memória)",
    "tempo": "apertar (reduzir perda — tempo)",
    "stop": "stop original",
    "stop_be": "stop no breakeven",
    "stop_trail": "trailing stop",
    "stop_apertar": "stop apertado (memória)",
    "stop_tempo": "stop apertado (tempo)",
    "target": "alvo atingido",
    "fechamento": "fechamento forçado",
}


def print_stop_report(result, cfg: dict) -> None:
    events = result.stop_events
    trades = result.trades
    if not cfg.get("stop_dinamico"):
        print("  stop_dinamico: desligado — use config.crt-tbs-dinamico.yaml\n")
        return

    print(f"\n{'=' * 50}")
    print("  Stop dinâmico — resumo dos ajustes")
    print(f"{'=' * 50}")
    print(f"  Total de ajustes:    {len(events)}")
    por_motivo: dict[str, int] = {}
    for e in events:
        por_motivo[e.motivo] = por_motivo.get(e.motivo, 0) + 1
    for m, n in sorted(por_motivo.items()):
        print(f"    {MOTIVO_LABEL.get(m, m):35} {n}")

    por_saida: dict[str, int] = {}
    for t in trades:
        por_saida[t.motivo] = por_saida.get(t.motivo, 0) + 1
    print("\n  Saídas por motivo:")
    for m, n in sorted(por_saida.items()):
        print(f"    {MOTIVO_LABEL.get(m, m):35} {n}")
    print(f"{'=' * 50}\n")

    if events:
        print("Linha do tempo dos ajustes de stop:")
        for e in events:
            seta = "↑" if e.lado == "long" else "↓"
            print(
                f"  [{str(e.barra)[:16]}] {e.lado:5} {seta} "
                f"{e.stop_de:.5f} → {e.stop_para:.5f} | "
                f"{MOTIVO_LABEL.get(e.motivo, e.motivo)} | "
                f"{e.profit_r:+.2f}R conf={e.confianca:.2f}"
            )
        print()

    if trades:
        print("Operações (stop inicial → final):")
        for i, t in enumerate(trades, 1):
            sinal = "+" if t.lucro > 0 else ""
            print(
                f"  {i}. {t.lado:5} {str(t.entrada)[:16]} → {str(t.saida)[:16]} | "
                f"{sinal}R$ {t.lucro:.2f} ({MOTIVO_LABEL.get(t.motivo, t.motivo)}) | "
                f"stop {t.stop_inicial:.5f}→{t.stop_final:.5f} ({t.ajustes_stop} ajustes)"
            )
        print()


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
                f"{sinal}R$ {t.lucro:.2f} ({MOTIVO_LABEL.get(t.motivo, t.motivo)}) "
                f"conf={t.confianca:.2f}"
            )
        print()


def cmd_simular_stop(cfg: dict, args: argparse.Namespace) -> int:
    """Simula stop dinâmico com log detalhado de cada ajuste."""
    symbol = args.symbol or cfg["symbol"]
    estrategia = args.estrategia or cfg.get("estrategia", "ema_rsi")
    interval = cfg.get("interval", "1h")
    dias = args.dias
    cfg = {**cfg, "estrategia": estrategia}

    if not cfg.get("stop_dinamico"):
        print("AVISO: stop_dinamico=false neste config. Use config.crt-tbs-dinamico.yaml")

    df = fetch(symbol, period="1mo", interval=interval)
    cutoff = df.index[-1] - pd.Timedelta(days=dias)
    df_m = df[df.index >= cutoff].copy()

    print(f"Simulação stop dinâmico — últimos {dias} dias")
    print(f"  {symbol} | {interval} | {estrategia}")
    print(f"  Breakeven: {cfg.get('breakeven_apos_rr', 0.5)}R | "
          f"Trailing: {cfg.get('trailing_apos_rr', 1.0)}R")
    print(f"  Apertar perda: conf<{cfg.get('apertar_se_confianca_abaixo', 0.4)} | "
          f"após {cfg.get('apertar_apos_barras', 0)} barras")
    print(f"  De {df_m.index[0]} até {df_m.index[-1]} ({len(df_m)} candles)")

    result = run_backtest(df_m, cfg)
    print_report(result, symbol, cfg["capital_inicial"], estrategia)
    print_stop_report(result, cfg)
    return 0


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


def cmd_simular_mes(cfg: dict, args: argparse.Namespace) -> int:
    symbol = args.symbol or cfg["symbol"]
    estrategia = args.estrategia or cfg.get("estrategia", "ema_rsi")
    interval = cfg.get("interval", "1h")
    dias = args.dias
    cfg = {**cfg, "estrategia": estrategia}

    df = fetch(symbol, period="1mo", interval=interval)
    cutoff = df.index[-1] - pd.Timedelta(days=dias)
    df_m = df[df.index >= cutoff].copy()

    print(f"Simulação — últimos {dias} dias")
    print(f"  {symbol} | {interval} | {estrategia} | memória adaptativa: sim")
    print(f"  De {df_m.index[0]} até {df_m.index[-1]} ({len(df_m)} candles)\n")

    result = run_backtest(df_m, cfg)
    print_report(result, symbol, cfg["capital_inicial"], estrategia)

    if result.trades:
        print("Todas as operações do período:")
        for i, t in enumerate(result.trades, 1):
            sinal = "+" if t.lucro > 0 else ""
            print(
                f"  {i}. {t.lado:5} {str(t.entrada)[:16]} → {str(t.saida)[:16]} | "
                f"{sinal}R$ {t.lucro:.2f} ({t.motivo})"
            )
    return 0


def cmd_mt5_test(cfg: dict, args: argparse.Namespace) -> int:
    from src.mt5_session import Mt5Session
    from src.brokers.mt5_broker import Mt5Broker

    symbol = args.symbol or cfg.get("mt5_symbol", cfg.get("symbol", "EURUSD"))
    print("Testando conexão MetaTrader 5 (FBS)...\n")

    acc = Mt5Session.account_info(cfg)
    print(f"  Login:    {acc['login']}")
    print(f"  Servidor: {acc['server']}")
    print(f"  Saldo:    {acc['balance']:.2f} {acc['currency']}")
    print(f"  Equity:   {acc['equity']:.2f}")

    broker = Mt5Broker(cfg)
    quote = broker.get_quote(symbol)
    print(f"\n  Símbolo:  {quote.symbol}")
    print(f"  Preço:    {quote.price}")
    print(f"  Hora:     {quote.timestamp}")
    print("\nConexão OK. Use: python run.py paper -c config.fbs.yaml --once")
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
        choices=[
            "ema_rsi", "macd_bb", "rsi_bb", "ema_pullback", "bb_reversion",
            "ema_cross", "bb_active", "rsi_cross", "scalp_momentum", "crt_tbs",
        ],
        help="Estratégia de sinais",
    )

    p_paper = sub.add_parser("paper", help="Paper trading em tempo real")
    p_paper.add_argument("--symbol", help="Símbolo")
    p_paper.add_argument(
        "--estrategia",
        choices=[
            "ema_rsi", "macd_bb", "rsi_bb", "ema_pullback", "bb_reversion",
            "ema_cross", "bb_active", "rsi_cross",
        ],
    )
    p_paper.add_argument(
        "--once",
        action="store_true",
        help="Executa um único ciclo (útil para teste)",
    )

    p_mt5 = sub.add_parser("mt5-test", help="Testa conexão FBS/MT5 (Windows)")
    p_mt5.add_argument("--symbol", help="Símbolo MT5 (ex: EURUSD)")

    p_sim = sub.add_parser("simular-mes", help="Backtest só no último mês (~30 dias)")
    p_sim.add_argument("--symbol", help="Símbolo")
    p_sim.add_argument("--dias", type=int, default=30, help="Janela em dias (padrão 30)")
    p_sim.add_argument(
        "--estrategia",
        choices=[
            "ema_rsi", "macd_bb", "rsi_bb", "ema_pullback", "bb_reversion",
            "ema_cross", "bb_active", "rsi_cross", "scalp_momentum", "crt_tbs",
        ],
    )

    p_stop = sub.add_parser(
        "simular-stop",
        help="Simula stop dinâmico com log de cada ajuste (proteger lucro / reduzir perda)",
    )
    p_stop.add_argument("--symbol", help="Símbolo")
    p_stop.add_argument("--dias", type=int, default=30, help="Janela em dias (padrão 30)")
    p_stop.add_argument(
        "--estrategia",
        choices=[
            "ema_rsi", "macd_bb", "rsi_bb", "ema_pullback", "bb_reversion",
            "ema_cross", "bb_active", "rsi_cross", "scalp_momentum", "crt_tbs",
        ],
    )

    args = parser.parse_args()
    cfg = load_config(args.config)

    if args.command == "backtest":
        return cmd_backtest(cfg, args)
    if args.command == "paper":
        return cmd_paper(cfg, args)
    if args.command == "mt5-test":
        return cmd_mt5_test(cfg, args)
    if args.command == "simular-mes":
        return cmd_simular_mes(cfg, args)
    if args.command == "simular-stop":
        return cmd_simular_stop(cfg, args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

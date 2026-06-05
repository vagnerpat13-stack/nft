#!/usr/bin/env python3
"""Varre estratégias e parâmetros em busca de maior taxa de acerto."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest import run_backtest
from src.data import fetch
from src.engine import TradingEngine
from src.indicators import bollinger, ema, enrich_ema_rsi, rsi
from src.strategies.base import BaseStrategy
from src.strategy import Side


@dataclass
class Result:
    nome: str
    symbol: str
    interval: str
    ops: int
    winrate: float
    retorno: float
    pf: float
    tp: float
    sl: float


class RsiReversionStrategy(BaseStrategy):
    name = "rsi_reversion"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        p = cfg.get("rsi_periodo", 14)
        out["rsi"] = rsi(out["Close"], p)
        out["ema200"] = ema(out["Close"], cfg.get("ema_filtro", 50))
        out["trend"] = (out["Close"] - out["ema200"]) / out["Close"]
        out["volatility"] = out["Close"].pct_change().rolling(14).std().fillna(0.02)
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        os_level = cfg.get("rsi_oversold", 30)
        ob_level = cfg.get("rsi_overbought", 70)
        use_trend = cfg.get("rsi_usar_tendencia", True)
        if row["rsi"] < os_level:
            if use_trend and row["Close"] < row["ema200"]:
                return None
            return "long"
        if row["rsi"] > ob_level:
            if use_trend and row["Close"] > row["ema200"]:
                return None
            return "short"
        return None


class BbReversionStrategy(BaseStrategy):
    name = "bb_reversion"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        bb = bollinger(out["Close"], cfg.get("bb_periodo", 20), cfg.get("bb_desvio", 2.0))
        out = pd.concat([out, bb], axis=1)
        out["rsi"] = rsi(out["Close"], 14)
        out["trend"] = (out["Close"] - out["bb_mid"]) / out["Close"]
        out["volatility"] = (out["bb_upper"] - out["bb_lower"]) / out["Close"]
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("bb_mid"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        if row["Close"] <= row["bb_lower"] and prev["Close"] > prev["bb_lower"]:
            return "long"
        if row["Close"] >= row["bb_upper"] and prev["Close"] < prev["bb_upper"]:
            return "short"
        return None


class RsiBbStrategy(BaseStrategy):
    name = "rsi_bb"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        out = df.copy()
        bb = bollinger(out["Close"], 20, 2.0)
        out = pd.concat([out, bb], axis=1)
        out["rsi"] = rsi(out["Close"], 14)
        out["trend"] = (out["Close"] - out["bb_mid"]) / out["Close"]
        out["volatility"] = (out["bb_upper"] - out["bb_lower"]) / out["Close"]
        return out

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        if row["rsi"] < 32 and row["Close"] <= row["bb_lower"] * 1.005:
            return "long"
        if row["rsi"] > 68 and row["Close"] >= row["bb_upper"] * 0.995:
            return "short"
        return None


class EmaPullbackStrategy(BaseStrategy):
    name = "ema_pullback"

    def enrich(self, df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
        return enrich_ema_rsi(df, 9, 21, 14)

    def _row_ready(self, row: pd.Series) -> bool:
        return not pd.isna(row.get("rsi"))

    def raw_signal(self, row: pd.Series, prev: pd.Series, cfg: dict) -> Side | None:
        uptrend = row["ema_fast"] > row["ema_slow"]
        downtrend = row["ema_fast"] < row["ema_slow"]
        if uptrend and 35 <= row["rsi"] <= 48 and prev["rsi"] < row["rsi"]:
            return "long"
        if downtrend and 52 <= row["rsi"] <= 65 and prev["rsi"] > row["rsi"]:
            return "short"
        return None


def run_one(
    strategy: BaseStrategy,
    df: pd.DataFrame,
    base_cfg: dict,
    tp: float,
    sl: float,
    symbol: str,
    interval: str,
    adaptive: bool,
) -> Result:
    cfg = {
        **base_cfg,
        "take_profit_pct": tp,
        "stop_loss_pct": sl,
        "confianca_minima": 0.45 if adaptive else 0.0,
    }
    enriched = strategy.enrich(df, cfg)
    engine = TradingEngine(strategy, cfg)
    engine.run_series(enriched)
    m = engine.metrics()
    ret = (m["capital_final"] / base_cfg["capital_inicial"] - 1) * 100
    return Result(
        nome=strategy.name,
        symbol=symbol,
        interval=interval,
        ops=m["total_operacoes"],
        winrate=m["taxa_acerto"],
        retorno=ret,
        pf=m["profit_factor"],
        tp=tp,
        sl=sl,
    )


def main() -> None:
    base_cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    base_cfg["penalidade_erro"] = 0.12
    base_cfg["bonus_acerto"] = 0.04

    universes = [
        ("PETR4.SA", "1d", "2y"),
        ("VALE3.SA", "1d", "2y"),
        ("EURUSD=X", "1h", "730d"),
        ("EURUSD=X", "1d", "2y"),
    ]

    strategies: list[BaseStrategy] = [
        RsiReversionStrategy(),
        BbReversionStrategy(),
        RsiBbStrategy(),
        EmaPullbackStrategy(),
    ]

    risk_profiles = [
        (0.06, 0.03),
        (0.03, 0.03),
        (0.02, 0.04),
        (0.015, 0.03),
        (0.01, 0.02),
    ]

    results: list[Result] = []

    for symbol, interval, period in universes:
        try:
            df = fetch(symbol, period=period, interval=interval)
        except Exception as e:
            print(f"Skip {symbol} {interval}: {e}")
            continue
        for strat in strategies:
            for tp, sl in risk_profiles:
                for adaptive in (True, False):
                    r = run_one(strat, df, base_cfg, tp, sl, symbol, interval, adaptive)
                    if r.ops >= 5:
                        results.append(r)

    results.sort(key=lambda x: (-x.winrate, -x.ops, x.retorno))

    print("\n=== TOP 15 por taxa de acerto (mín. 5 operações) ===\n")
    print(
        f"{'#':<3} {'Estratégia':<14} {'Ativo':<10} {'TF':<4} "
        f"{'Ops':>4} {'Acerto%':>8} {'Ret%':>8} {'PF':>5} {'TP/SL':>10}"
    )
    print("-" * 72)
    for i, r in enumerate(results[:15], 1):
        print(
            f"{i:<3} {r.nome:<14} {r.symbol:<10} {r.interval:<4} "
            f"{r.ops:>4} {r.winrate:>7.1f}% {r.retorno:>+7.2f}% {r.pf:>5.2f} "
            f"{r.tp:.0%}/{r.sl:.0%}"
        )

    profitable = [r for r in results if r.retorno > 0 and r.ops >= 5]
    profitable.sort(key=lambda x: (-x.winrate, -x.retorno))
    print("\n=== Melhor equilíbrio: acerto alto E retorno positivo ===\n")
    if not profitable:
        print("Nenhuma combinação com retorno positivo e >= 5 ops neste universo.")
    else:
        for r in profitable[:5]:
            print(
                f"  {r.nome} | {r.symbol} {r.interval} | "
                f"acerto {r.winrate:.1f}% | retorno {r.retorno:+.2f}% | "
                f"ops {r.ops} | TP/SL {r.tp:.0%}/{r.sl:.0%}"
            )


if __name__ == "__main__":
    main()

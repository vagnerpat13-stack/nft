"""Motor de backtest com adaptação contínua aos erros."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .adaptive import AdaptiveMemory, SignalContext
from .indicators import enrich
from .risk import RiskConfig, check_exit, open_position, pnl
from .strategy import Signal, raw_signal


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
class BacktestResult:
    trades: list[TradeRecord] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)
    capital_final: float = 0.0
    taxa_acerto: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    total_operacoes: int = 0
    memoria: dict = field(default_factory=dict)


def _signal_at_bar(
    enriched: pd.DataFrame,
    i: int,
    memory: AdaptiveMemory,
    rsi_ob: float,
    rsi_os: float,
) -> Signal | None:
    if i < 1:
        return None
    row, prev = enriched.iloc[i], enriched.iloc[i - 1]
    if pd.isna(row["rsi"]) or pd.isna(row["ema_slow"]):
        return None

    side = raw_signal(row, prev, rsi_ob, rsi_os)
    if side is None:
        return None

    ctx = SignalContext(
        side=side,
        trend=float(row["trend"]),
        rsi=float(row["rsi"]),
        volatility=float(row["volatility"]),
    )
    if not memory.aceita(ctx):
        return None

    return Signal(
        index=i,
        side=side,
        price=float(row["Close"]),
        confianca=memory.confianca(ctx),
        context=ctx,
    )


def run_backtest(df: pd.DataFrame, cfg: dict) -> BacktestResult:
    enriched = enrich(
        df,
        cfg["ema_rapida"],
        cfg["ema_lenta"],
        cfg["rsi_periodo"],
    )

    memory = AdaptiveMemory(
        penalidade_erro=cfg["penalidade_erro"],
        bonus_acerto=cfg["bonus_acerto"],
        decaimento=cfg["decaimento_memoria"],
        confianca_minima=cfg["confianca_minima"],
    )

    risk = RiskConfig(
        capital=cfg["capital_inicial"],
        risco_por_operacao=cfg["risco_por_operacao"],
        stop_loss_pct=cfg["stop_loss_pct"],
        take_profit_pct=cfg["take_profit_pct"],
        max_operacoes_dia=cfg["max_operacoes_dia"],
        drawdown_max_pct=cfg["drawdown_max_pct"],
    )

    capital = risk.capital
    peak = capital
    max_dd = 0.0
    equity = [capital]
    trades: list[TradeRecord] = []
    position = None
    ops_no_dia: dict[str, int] = {}

    for i in range(len(enriched)):
        row = enriched.iloc[i]
        date_key = str(row.name)[:10]

        if peak > 0 and capital <= peak * (1 - risk.drawdown_max_pct):
            break

        if position is not None:
            exit_info = check_exit(
                position,
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
            )
            if exit_info is None and i == len(enriched) - 1:
                exit_info = (float(row["Close"]), "fim_serie")

            if exit_info:
                exit_price, motivo = exit_info
                lucro = pnl(position, exit_price)
                capital += lucro
                memory.registrar(position.context, lucro)

                trades.append(
                    TradeRecord(
                        entrada=str(enriched.index[position.entry_index]),
                        saida=str(row.name),
                        lado=position.side,
                        preco_entrada=position.entry_price,
                        preco_saida=exit_price,
                        lucro=round(lucro, 2),
                        motivo=motivo,
                        confianca=position.confianca_entrada,
                    )
                )
                position = None
                risk.capital = capital

        if position is None:
            sig = _signal_at_bar(
                enriched,
                i,
                memory,
                cfg["rsi_sobrecompra"],
                cfg["rsi_sobrevenda"],
            )
            if sig and ops_no_dia.get(date_key, 0) < risk.max_operacoes_dia:
                pos = open_position(
                    sig.side,
                    sig.price,
                    i,
                    risk,
                    sig.context,
                    sig.confianca,
                )
                if pos:
                    position = pos
                    ops_no_dia[date_key] = ops_no_dia.get(date_key, 0) + 1

        peak = max(peak, capital)
        dd = (peak - capital) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
        equity.append(capital)

    wins = [t for t in trades if t.lucro > 0]
    losses = [t for t in trades if t.lucro < 0]
    gross_win = sum(t.lucro for t in wins) or 0.01
    gross_loss = abs(sum(t.lucro for t in losses)) or 0.01

    return BacktestResult(
        trades=trades,
        equity_curve=equity,
        capital_final=round(capital, 2),
        taxa_acerto=round(len(wins) / len(trades) * 100, 2) if trades else 0.0,
        profit_factor=round(gross_win / gross_loss, 2),
        max_drawdown_pct=round(max_dd * 100, 2),
        total_operacoes=len(trades),
        memoria=memory.resumo(),
    )

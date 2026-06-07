"""Stop dinâmico: proteger lucro e reduzir perda (agente + memória adaptativa)."""

from __future__ import annotations

from .adaptive import AdaptiveMemory
from .risk import Position


def _initial_risk(pos: Position) -> float:
    if pos.initial_stop:
        return abs(pos.entry_price - pos.initial_stop)
    return abs(pos.entry_price - pos.stop)


def _profit_r(pos: Position, price: float) -> float:
    risk = _initial_risk(pos)
    if risk <= 0:
        return 0.0
    if pos.side == "long":
        return (price - pos.entry_price) / risk
    return (pos.entry_price - price) / risk


def adjust_dynamic_stop(
    pos: Position,
    high: float,
    low: float,
    close: float,
    cfg: dict,
    memory: AdaptiveMemory,
    bars_open: int,
) -> str | None:
    """
    Ajusta pos.stop in-place. Retorna motivo do ajuste (ou None).
    Só move stop na direção favorável (long: stop sobe; short: stop desce).
    """
    if not cfg.get("stop_dinamico", False):
        return None

    entry = pos.entry_price
    risk = _initial_risk(pos)
    if risk <= 0:
        return None

    if pos.side == "long":
        pos.best_price = max(pos.best_price or entry, high)
        fav_price = pos.best_price
        profit_r = (fav_price - entry) / risk
        unrealized_r = (close - entry) / risk
    else:
        pos.best_price = min(pos.best_price or entry, low)
        fav_price = pos.best_price
        profit_r = (entry - fav_price) / risk
        unrealized_r = (entry - close) / risk

    conf_now = memory.confianca(pos.context)
    reason: str | None = None
    new_stop = pos.stop

    # --- Proteger lucro: breakeven ---
    be_rr = float(cfg.get("breakeven_apos_rr", 0.5))
    be_buf = float(cfg.get("breakeven_buffer_pct", 0.0002))
    if profit_r >= be_rr:
        if pos.side == "long":
            be_stop = entry * (1 + be_buf)
            if be_stop > new_stop:
                new_stop = be_stop
                reason = "be"
        else:
            be_stop = entry * (1 - be_buf)
            if be_stop < new_stop:
                new_stop = be_stop
                reason = "be"

    # --- Proteger lucro: trailing ---
    trail_rr = float(cfg.get("trailing_apos_rr", 1.0))
    trail_pct = float(cfg.get("trailing_dist_pct", 0.003))
    if profit_r >= trail_rr:
        if pos.side == "long":
            trail_stop = fav_price * (1 - trail_pct)
            if trail_stop > new_stop:
                new_stop = trail_stop
                reason = "trail"
        else:
            trail_stop = fav_price * (1 + trail_pct)
            if trail_stop < new_stop:
                new_stop = trail_stop
                reason = "trail"

    # --- Reduzir perda: memória adaptativa (confiança caiu) ---
    if cfg.get("apertar_stop_adaptativo", True) and unrealized_r < 0:
        conf_min = float(cfg.get("apertar_se_confianca_abaixo", 0.40))
        conf_drop = float(cfg.get("apertar_queda_confianca", 0.08))
        if conf_now < conf_min or conf_now < pos.confianca_entrada - conf_drop:
            perda_rr = float(cfg.get("apertar_perda_rr", -0.25))
            if unrealized_r <= perda_rr:
                fator = float(cfg.get("apertar_fator", 0.5))
                if pos.side == "long":
                    urgente = entry - (entry - pos.initial_stop) * fator
                    if urgente > new_stop and urgente < close:
                        new_stop = urgente
                        reason = "apertar"
                else:
                    urgente = entry + (pos.initial_stop - entry) * fator
                    if urgente < new_stop and urgente > close:
                        new_stop = urgente
                        reason = "apertar"

    # --- Reduzir perda: tempo em trade sem progresso ---
    max_bars = int(cfg.get("apertar_apos_barras", 0))
    if max_bars > 0 and bars_open >= max_bars and unrealized_r < 0:
        fator = float(cfg.get("apertar_fator_tempo", 0.6))
        if pos.side == "long":
            urgente = entry - (entry - pos.initial_stop) * fator
            if urgente > new_stop:
                new_stop = urgente
                reason = "tempo"
        else:
            urgente = entry + (pos.initial_stop - entry) * fator
            if urgente < new_stop:
                new_stop = urgente
                reason = "tempo"

    if new_stop != pos.stop:
        pos.stop = new_stop
        pos.last_stop_adjust = reason
        return reason
    return None


def exit_motivo(base: str, last_adjust: str | None) -> str:
    if base == "stop" and last_adjust:
        return f"stop_{last_adjust}"
    return base

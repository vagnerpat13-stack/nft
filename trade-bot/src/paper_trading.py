"""Paper trading em tempo real (simulado ou Alpaca)."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from .brokers import get_broker
from .brokers.base import BaseBroker
from .data import fetch_recent


def _fetch_candles(cfg: dict, symbol: str):
    broker = cfg.get("broker", "simulado").lower()
    fonte = cfg.get("fonte_dados", "auto").lower()
    use_mt5 = fonte == "mt5" or broker in ("mt5", "fbs", "metatrader", "metatrader5")
    if fonte == "yfinance":
        use_mt5 = False
    if use_mt5:
        from .data_mt5 import fetch_recent_mt5

        return fetch_recent_mt5(symbol, cfg)
    interval = cfg.get("paper_interval", cfg.get("interval", "5m"))
    period = cfg.get("paper_periodo", "5d")
    return fetch_recent(symbol, interval=interval, period=period)
from .engine import TradingEngine
from .state import PersistedState, load_state, save_state
from .strategies import get_strategy


def _state_path(cfg: dict) -> Path:
    return Path(cfg.get("arquivo_estado", "data/estado.json"))


def _build_engine(cfg: dict, symbol: str) -> tuple[TradingEngine, PersistedState | None]:
    strategy = get_strategy(cfg.get("estrategia", "ema_rsi"))
    path = _state_path(cfg)
    saved = load_state(path)

    engine = TradingEngine(strategy, cfg)
    if saved and saved.symbol == symbol and saved.estrategia == strategy.name:
        saved.apply_to_engine(engine, cfg)
    elif saved:
        print(f"Estado ignorado (símbolo/estratégia diferentes). Novo ciclo.")

    return engine, saved


def _sync_broker_open(broker: BaseBroker, symbol: str, engine: TradingEngine) -> None:
    pos = engine.state.position
    if pos is None:
        return
    result = broker.submit_market(
        symbol,
        pos.side,
        pos.quantity,
        stop=pos.stop,
        target=pos.target,
    )
    if result.ok:
        print(f"  [broker] Abertura {pos.side} @ {result.filled_price:.2f} id={result.order_id}")
    else:
        print(f"  [broker] Falha abertura: {result.message}")


def _sync_broker_close(broker: BaseBroker, symbol: str) -> None:
    result = broker.close_position(symbol)
    if result and result.ok:
        print(f"  [broker] Fechamento @ {result.filled_price:.2f} — {result.message}")
    elif result:
        print(f"  [broker] Falha fechamento: {result.message}")


def run_paper_cycle(cfg: dict, symbol: str, broker: BaseBroker | None = None) -> dict:
    """Executa um ciclo: baixa dados, processa último candle, salva estado."""
    strategy = get_strategy(cfg.get("estrategia", "ema_rsi"))
    df = _fetch_candles(cfg, symbol)
    enriched = strategy.enrich(df, cfg)
    if len(enriched) < 2:
        return {"status": "dados_insuficientes"}

    engine, _ = _build_engine(cfg, symbol)
    last_ts = str(enriched.index[-1])
    path = _state_path(cfg)
    saved = load_state(path)

    if saved and saved.last_bar_ts == last_ts:
        return {"status": "sem_novo_candle", "ultimo": last_ts}

    i = len(enriched) - 1
    had_position = engine.state.position is not None
    result = engine.step(enriched, i)

    if broker:
        if result.trade_closed and had_position:
            _sync_broker_close(broker, symbol)
        if result.position_opened:
            _sync_broker_open(broker, symbol, engine)

    persisted = PersistedState.from_engine(engine, symbol, strategy.name, last_ts)
    save_state(path, persisted)

    out = {
        "status": "ok",
        "candle": last_ts,
        "capital": engine.state.capital,
        "posicao": engine.state.position.side if engine.state.position else None,
        "trade_fechado": result.trade_closed.lucro if result.trade_closed else None,
        "memoria": engine.memory.resumo(),
    }
    return out


def run_paper_loop(cfg: dict, symbol: str, once: bool = False) -> None:
    broker_name = cfg.get("broker", "simulado")
    broker = None
    if broker_name != "interno":
        broker = get_broker(broker_name, cfg)
        cash = broker.get_cash()
        print(f"Broker: {broker_name} | Saldo: {cash:.2f}")
        if broker_name in ("mt5", "fbs"):
            from .mt5_session import Mt5Session

            acc = Mt5Session.account_info(cfg)
            print(f"  Conta MT5: {acc['login']} @ {acc['server']} ({acc['currency']})")

    intervalo = int(cfg.get("paper_poll_segundos", 300))
    print(f"Paper trading — {symbol} | estratégia: {cfg.get('estrategia')}")
    print(f"Poll a cada {intervalo}s (Ctrl+C para parar)\n")

    while True:
        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            info = run_paper_cycle(cfg, symbol, broker)
            print(f"[{now}] {info}")
            if once:
                break
            time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nEncerrado pelo usuário.")
            break

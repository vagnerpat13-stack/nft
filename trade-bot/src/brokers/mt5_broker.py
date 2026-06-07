"""Corretora via MetaTrader 5 — FBS, demo ou real."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..mt5_session import Mt5Session
from .base import BaseBroker, OrderResult, Quote, Side


@dataclass
class Mt5Broker(BaseBroker):
    """Envia ordens ao terminal MT5 logado na FBS (ou outra corretora MT5)."""

    cfg: dict
    magic: int = field(default=0)

    def __post_init__(self) -> None:
        self.magic = int(self.cfg.get("mt5_magic", 202606))
        Mt5Session.ensure(self.cfg)

    def _symbol(self, symbol: str) -> str:
        return self.cfg.get("mt5_symbol", symbol)

    def _volume_lots(self, quantity: float, symbol: str) -> float:
        """MT5 usa lotes; config mt5_lote tem prioridade sobre quantity do engine."""
        if "mt5_lote" in self.cfg:
            return float(self.cfg["mt5_lote"])
        mt5 = Mt5Session.ensure(self.cfg)
        sym = self._symbol(symbol)
        info = mt5.symbol_info(sym)
        if info is None:
            return max(0.01, round(quantity, 2))
        step = info.volume_step or 0.01
        vol = max(info.volume_min, min(quantity, info.volume_max))
        steps = round(vol / step)
        return round(steps * step, 2)

    def get_quote(self, symbol: str) -> Quote:
        mt5 = Mt5Session.ensure(self.cfg)
        sym = self._symbol(symbol)
        tick = mt5.symbol_info_tick(sym)
        if tick is None:
            raise RuntimeError(f"Sem cotação para {sym}: {mt5.last_error()}")
        price = float(tick.last) or float(tick.bid)
        return Quote(
            symbol=sym,
            price=price,
            high=price,
            low=price,
            timestamp=str(tick.time),
        )

    def get_cash(self) -> float:
        info = Mt5Session.account_info(self.cfg)
        return float(info["balance"])

    def _filling_mode(self, mt5, sym: str) -> int:
        info = mt5.symbol_info(sym)
        if info is None:
            return mt5.ORDER_FILLING_IOC
        filling = info.filling_mode
        if filling & mt5.SYMBOL_FILLING_IOC:
            return mt5.ORDER_FILLING_IOC
        if filling & mt5.SYMBOL_FILLING_FOK:
            return mt5.ORDER_FILLING_FOK
        return mt5.ORDER_FILLING_RETURN

    def submit_market(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        stop: float | None = None,
        target: float | None = None,
    ) -> OrderResult:
        mt5 = Mt5Session.ensure(self.cfg)
        sym = self._symbol(symbol)
        tick = mt5.symbol_info_tick(sym)
        if tick is None:
            return OrderResult(False, "", 0, 0, str(mt5.last_error()))

        volume = self._volume_lots(quantity, symbol)
        order_type = mt5.ORDER_TYPE_BUY if side == "long" else mt5.ORDER_TYPE_SELL
        price = tick.ask if side == "long" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": sym,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": int(self.cfg.get("mt5_desvio_pontos", 20)),
            "magic": self.magic,
            "comment": self.cfg.get("mt5_comentario", "trade-bot"),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": self._filling_mode(mt5, sym),
        }
        if stop:
            request["sl"] = float(stop)
        if target:
            request["tp"] = float(target)

        result = mt5.order_send(request)
        if result is None:
            return OrderResult(False, "", 0, 0, str(mt5.last_error()))
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return OrderResult(
                False,
                str(result.order),
                0,
                0,
                f"{result.retcode}: {result.comment}",
            )
        return OrderResult(
            True,
            str(result.order),
            float(result.price),
            volume,
            result.comment,
        )

    def close_position(self, symbol: str) -> OrderResult | None:
        mt5 = Mt5Session.ensure(self.cfg)
        sym = self._symbol(symbol)
        positions = mt5.positions_get(symbol=sym)
        if not positions:
            return None

        closed = []
        for pos in positions:
            if pos.magic != self.magic and self.cfg.get("mt5_fechar_apenas_magic", True):
                continue
            tick = mt5.symbol_info_tick(sym)
            if tick is None:
                continue
            if pos.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": sym,
                "volume": pos.volume,
                "type": order_type,
                "position": pos.ticket,
                "price": price,
                "deviation": int(self.cfg.get("mt5_desvio_pontos", 20)),
                "magic": self.magic,
                "comment": "trade-bot-close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": self._filling_mode(mt5, sym),
            }
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                closed.append(str(result.order))

        if not closed:
            return OrderResult(False, "", 0, 0, "Nenhuma posição fechada (verifique magic/símbolo)")
        return OrderResult(True, ",".join(closed), 0, 0, "posição encerrada no MT5")

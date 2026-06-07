"""Integração Alpaca Markets (paper trading — ações EUA)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import requests

from .base import BaseBroker, OrderResult, Quote, Side

PAPER_BASE = "https://paper-api.alpaca.markets"
DATA_BASE = "https://data.alpaca.markets/v2"


@dataclass
class AlpacaBroker(BaseBroker):
    cfg: dict
    api_key: str = field(default="")
    api_secret: str = field(default="")
    base_url: str = PAPER_BASE

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("APCA_API_KEY_ID", "")
        self.api_secret = self.api_secret or os.environ.get("APCA_API_SECRET_KEY", "")
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "Alpaca: defina APCA_API_KEY_ID e APCA_API_SECRET_KEY no ambiente."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
        }

    def _get(self, path: str, params: dict | None = None) -> dict:
        r = requests.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params or {},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> dict:
        r = requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=body,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def get_cash(self) -> float:
        acc = self._get("/v2/account")
        return float(acc.get("cash", 0))

    def get_quote(self, symbol: str) -> Quote:
        sym = symbol.replace(".SA", "").upper()
        r = requests.get(
            f"{DATA_BASE}/stocks/{sym}/bars/latest",
            headers=self._headers(),
            timeout=30,
        )
        r.raise_for_status()
        bar = r.json().get("bar", r.json())
        price = float(bar["c"])
        return Quote(
            symbol=sym,
            price=price,
            high=float(bar.get("h", price)),
            low=float(bar.get("l", price)),
            timestamp=str(bar.get("t", "")),
        )

    def submit_market(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        stop: float | None = None,
        target: float | None = None,
    ) -> OrderResult:
        sym = symbol.replace(".SA", "").upper()
        alpaca_side = "buy" if side == "long" else "sell"
        try:
            data = self._post(
                "/v2/orders",
                {
                    "symbol": sym,
                    "qty": str(int(quantity)) if quantity >= 1 else str(round(quantity, 4)),
                    "side": alpaca_side,
                    "type": "market",
                    "time_in_force": "day",
                },
            )
            return OrderResult(
                True,
                data.get("id", ""),
                float(data.get("filled_avg_price") or 0),
                float(data.get("filled_qty") or quantity),
                data.get("status", "submitted"),
            )
        except requests.HTTPError as e:
            return OrderResult(False, "", 0, 0, str(e))

    def close_position(self, symbol: str) -> OrderResult | None:
        sym = symbol.replace(".SA", "").upper()
        try:
            r = requests.delete(
                f"{self.base_url}/v2/positions/{sym}",
                headers=self._headers(),
                timeout=30,
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return OrderResult(True, "close", 0, 0, "posição encerrada")
        except requests.HTTPError as e:
            return OrderResult(False, "", 0, 0, str(e))

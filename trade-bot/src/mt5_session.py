"""Sessão compartilhada com o terminal MetaTrader 5 (FBS e outras corretoras)."""

from __future__ import annotations

import os
from typing import Any


class Mt5Session:
    _initialized = False

    @classmethod
    def ensure(cls, cfg: dict) -> Any:
        """Inicializa MT5 e faz login se credenciais existirem."""
        try:
            import MetaTrader5 as mt5
        except ImportError as e:
            raise ImportError(
                "Pacote MetaTrader5 não instalado. No Windows: pip install MetaTrader5\n"
                "O terminal FBS MT5 precisa estar aberto e logado."
            ) from e

        if not cls._initialized:
            path = cfg.get("mt5_path") or os.environ.get("MT5_PATH", "")
            ok = mt5.initialize(path=path) if path else mt5.initialize()
            if not ok:
                err = mt5.last_error()
                raise RuntimeError(
                    f"Falha ao conectar ao MetaTrader 5: {err}. "
                    "Abra o terminal FBS MT5 antes de rodar o robô."
                )

            login = int(os.environ.get("MT5_LOGIN", cfg.get("mt5_login", 0)) or 0)
            password = os.environ.get("MT5_PASSWORD", cfg.get("mt5_password", ""))
            server = os.environ.get("MT5_SERVER", cfg.get("mt5_server", ""))

            if login and password and server:
                if not mt5.login(login, password=password, server=server):
                    err = mt5.last_error()
                    mt5.shutdown()
                    cls._initialized = False
                    raise RuntimeError(f"Login MT5 falhou: {err}")

            cls._initialized = True

        return mt5

    @classmethod
    def shutdown(cls) -> None:
        if not cls._initialized:
            return
        try:
            import MetaTrader5 as mt5

            mt5.shutdown()
        except ImportError:
            pass
        cls._initialized = False

    @classmethod
    def account_info(cls, cfg: dict) -> dict:
        mt5 = cls.ensure(cfg)
        acc = mt5.account_info()
        if acc is None:
            raise RuntimeError(f"Sem conta MT5: {mt5.last_error()}")
        return {
            "login": acc.login,
            "server": acc.server,
            "balance": acc.balance,
            "equity": acc.equity,
            "currency": acc.currency,
            "trade_mode": acc.trade_mode,
        }

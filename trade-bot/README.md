# Robô de Trade Adaptativo

Sistema com **backtest**, **paper trading** em tempo real, **duas estratégias** e integração opcional com **Alpaca** (ações EUA).

> **Aviso:** Nenhum robô garante alta taxa de acerto. Teste em backtest e paper antes de usar capital real. B3: PETR4.SA via yfinance. EUA: AAPL via Alpaca paper.

## Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| **Adaptação** | Penaliza regimes que geraram perda; bloqueia sinais similares |
| **Backtest** | Histórico yfinance |
| **Paper** | Poll periódico, estado salvo em `data/estado.json` |
| **Estratégias** | `ema_rsi` (EMA + RSI), `macd_bb` (MACD + Bollinger) |
| **Brokers** | `simulado`, `alpaca` (EUA), **`mt5`** (FBS / MetaTrader 5) |

## Instalação

```bash
cd trade-bot
pip install -r requirements.txt
```

## Backtest

```bash
python run.py backtest
python run.py backtest --symbol VALE3.SA --period 1y
python run.py backtest --estrategia macd_bb --symbol PETR4.SA
```

## Paper trading (simulado — B3)

```bash
# Um ciclo (teste)
python run.py paper --once

# Loop contínuo (a cada 300s por padrão)
python run.py paper
python run.py paper --symbol PETR4.SA --estrategia ema_rsi
```

O estado (capital, memória adaptativa, posição aberta) é salvo em `data/estado.json`.

## FBS + MetaTrader 5 (Forex / CFD)

A FBS opera pelo **terminal MT5**. O robô conecta via biblioteca `MetaTrader5` no **Windows**.

**Guia completo:** [docs/FBS_METATRADER.md](docs/FBS_METATRADER.md)

Resumo:

1. Instale **FBS MetaTrader 5** e faça login (demo recomendado).
2. Ative **Negociação algorítmica** nas opções do MT5.
3. `pip install -r requirements-mt5.txt`
4. Configure `.env` com `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` (ex.: `FBS-Demo`).
5. Com o **MT5 aberto**:

```powershell
python run.py mt5-test -c config.fbs.yaml
python run.py paper -c config.fbs.yaml --once
```

Use `config.fbs.yaml` — volume em **lotes** (`mt5_lote: 0.01`), símbolo como no MT5 (`EURUSD`).

## Alpaca (ações EUA — paper)

1. Conta em [alpaca.markets](https://alpaca.markets) → chaves **Paper**
2. Copie `.env.example` para `.env` e preencha as chaves
3. Ajuste `config.yaml`:

```yaml
broker: alpaca
symbol: AAPL
estrategia: macd_bb
paper_interval: 5m
```

```bash
export $(grep -v '^#' .env | xargs)
python run.py paper --once
```

## Configuração principal

| Parâmetro | Função |
|-----------|--------|
| `estrategia` | `ema_rsi` ou `macd_bb` |
| `broker` | `simulado`, `alpaca` ou `mt5` (FBS) |
| `paper_poll_segundos` | Intervalo entre ciclos no paper |
| `confianca_minima` | Filtro adaptativo mínimo |
| `penalidade_erro` / `bonus_acerto` | Velocidade de aprendizado |

## Estrutura

```
trade-bot/
  run.py
  config.yaml
  .env.example
  data/estado.json      # gerado no paper
  src/
    engine.py           # Motor compartilhado
    paper_trading.py
    state.py
    strategies/         # ema_rsi, macd_bb
    brokers/            # simulado, alpaca
    backtest.py
```

## Relação com o repositório

Módulo separado do agente **Professor de Matemática SEE/MG**.

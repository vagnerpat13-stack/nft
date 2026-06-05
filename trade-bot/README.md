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
| **Brokers** | `simulado` (yfinance) ou `alpaca` (API paper) |

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
| `broker` | `simulado` ou `alpaca` |
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

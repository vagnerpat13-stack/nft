# Robô de Trade Adaptativo

Sistema com **backtest**, **paper trading** em tempo real, **duas estratégias** e integração opcional com **Alpaca** (ações EUA).

> **Aviso:** Nenhum robô garante alta taxa de acerto. Teste em backtest e paper antes de usar capital real. B3: PETR4.SA via yfinance. EUA: AAPL via Alpaca paper.

## Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| **Adaptação** | Penaliza regimes que geraram perda; bloqueia sinais similares |
| **Backtest** | Histórico yfinance |
| **Paper** | Poll periódico, estado salvo em `data/estado.json` |
| **Estratégias** | `ema_rsi`, `macd_bb`, **`rsi_bb`**, **`ema_pullback`**, `bb_reversion` |
| **Brokers** | `simulado`, `alpaca` (EUA), **`mt5`** (FBS / MetaTrader 5) |

## Instalação

```bash
cd trade-bot
pip install -r requirements.txt
```

## Estratégias com maior taxa de acerto (backtest interno)

| Estratégia | Melhor em | Taxa de acerto* | Retorno* |
|------------|-----------|-----------------|----------|
| **`rsi_bb`** | PETR4 diário, EURUSD 1h | ~78–79% | +3% a +11% |
| **`ema_pullback`** | EURUSD 1h (FBS) | **~83%** | +6% |
| `bb_reversion` | EURUSD 1h (muitas ops) | ~74% | +13% |

\*Com TP 2% / SL 4%, 2 anos de dados yfinance. **Passado ≠ futuro.**

```bash
# Ações BR (PETR4) — preset alta acerto
python run.py -c config.alta-acerto.yaml backtest

# FBS forex — preset ema_pullback
python run.py -c config.fbs-alta-acerto.yaml backtest  # + interval 1h no script
python run.py backtest --estrategia rsi_bb --symbol PETR4.SA
python run.py backtest --estrategia ema_pullback --symbol EURUSD=X --period 730d
```

**`rsi_bb`:** RSI &lt; 32 + preço na banda inferior → compra; RSI &gt; 68 + banda superior → venda.

**`ema_pullback`:** Tendência (EMA 9/21) + RSI em zona de pullback → entrada a favor da tendência.

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

## Forex R:R 1:3 (stop 1 → alvo 3)

Proporção **1:3** = se o stop perde 1%, o take profit busca 3% (`take_profit_pct = 3 × stop_loss_pct`).

| Estratégia | Par | SL / TP | Taxa de acerto* | Retorno* |
|------------|-----|---------|-----------------|----------|
| **`ema_pullback`** | GBPUSD 1h | 1% / 3% | **~45%** | +8,7% |
| **`ema_rsi`** | GBPUSD 1h | 1,5% / 4,5% | **~47%** | +21% |
| `bb_reversion` | GBPUSD 1h | 1,2% / 3,6% | ~45% | +16% |

\*Backtest ~2 anos (yfinance). Break-even teórico com 1:3 ≈ **25%** de acerto.

```bash
python run.py -c config.forex-rr13.yaml backtest
python run.py -c config.fbs-forex-rr13.yaml paper --once   # FBS MT5
python3 scripts/research_forex_rr13.py                     # repetir pesquisa
```

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

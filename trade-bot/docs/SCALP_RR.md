# Scalper com R:R 1:1,5 fixo

## O que significa 1:1,5

| | |
|--|--|
| **Risco (stop)** | 1 unidade (ex.: 0,4% do preço) |
| **Alvo (take profit)** | 1,5 unidades (ex.: 0,6% do preço) |

Break-even teórico: **40%** de taxa de acerto (`1 ÷ (1 + 1,5)`).

## Garantia no código

Com `rr_ratio: 1.5` no YAML, o robô **recalcula** sempre:

`take_profit_pct = stop_loss_pct × 1,5`

Mesmo que alguém edite só o stop, o alvo acompanha.

## Configuração

| Arquivo | Uso |
|---------|-----|
| `config.scalp.yaml` | Backtest / paper simulado |
| `config.fbs-scalp.yaml` | FBS MetaTrader 5 |

## Estratégia `scalp_momentum`

- EMA **5 / 13** (cruzamento rápido)
- RSI **7** confirma direção
- Stops curtos para fechar rápido e abrir nova operação

## Comandos

```bash
python run.py -c config.scalp.yaml backtest
python run.py -c config.scalp.yaml simular-mes
python run.py -c config.fbs-scalp.yaml paper --once
```

## Ajustar o stop (alvo segue sozinho)

```yaml
rr_ratio: 1.5
stop_loss_pct: 0.005   # alvo vira 0.0075 (0,75%)
```

## Mais operações

- `paper_interval: 15m` no config FBS
- `max_operacoes_dia: 20`
- `confianca_minima: 0.0` (desliga bloqueio adaptativo — mais risco)

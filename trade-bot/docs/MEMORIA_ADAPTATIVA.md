# Memória adaptativa — guia rápido

## O que faz

Após cada trade, o robô classifica o mercado em um **regime** (tendência, faixa de RSI, volatilidade, direção long/short) e:

- **Lucro** → aumenta confiança nesse regime  
- **Prejuízo** → reduz; abaixo de `confianca_minima` o regime é **bloqueado**

## Melhor estratégia para usar com adaptativo

| Prioridade | Estratégia | Mercado | Motivo |
|------------|------------|---------|--------|
| 1 | `ema_rsi` | GBPUSD 1h | Maior ganho com adaptativo nos testes |
| 2 | `ema_pullback` | GBPUSD 1h | Menos trades, acerto maior |
| 3 | `rsi_bb` | PETR4 1d | Protege contra reversões repetidas |

Evitar: `bb_reversion` (bloqueia demais), `macd_bb` (poucos sinais).

## Arquivos prontos

| Arquivo | Uso |
|---------|-----|
| `config.adaptativo.yaml` | Backtest / paper simulado |
| `config.fbs-adaptativo.yaml` | FBS MT5 em conta demo |

## Comandos

```bash
# Backtest
python run.py -c config.adaptativo.yaml backtest

# Último mês (~30 dias)
python run.py -c config.adaptativo.yaml simular-mes

# FBS (Windows + MT5 aberto)
python run.py mt5-test -c config.fbs-adaptativo.yaml
python run.py -c config.fbs-adaptativo.yaml paper --once
```

## Parâmetros da memória

| Parâmetro | Valor padrão | Efeito |
|-----------|--------------|--------|
| `confianca_minima` | 0.45 | Só opera se confiança ≥ 45% |
| `penalidade_erro` | 0.12 | Quanto cai após um stop |
| `bonus_acerto` | 0.04 | Quanto sobe após um alvo |
| `decaimento_memoria` | 0.995 | Esquecimento lento de regimes antigos |

## Estado salvo

`data/estado-adaptativo.json` ou `data/estado-fbs-adaptativo.json` guarda capital, scores por regime e posição aberta.

Não apague o arquivo se quiser continuar o aprendizado entre sessões.

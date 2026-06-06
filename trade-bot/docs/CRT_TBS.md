# CRT + TBS — Candle Range Theory + Turtle Body Soup

## Conceito (ICT / Smart Money)

| Sigla | Significado |
|-------|-------------|
| **CRT** | **Candle Range Theory** — usa o **high/low** de um candle de referência (dia ou 4h anterior) como range de liquidez |
| **TBS** | **Turtle Body Soup** — preço **sweep** (varre) o extremo do range e **fecha de volta** para dentro → armadilha / reversão |

### Fases (AMD)
1. **Accumulation** — preço dentro do range  
2. **Manipulation** — sweep acima/abaixo (pega stops)  
3. **Distribution** — movimento na direção oposta  

## Lógica implementada

**LONG (TBS na mínima do CRT):**
- Low < mínima do dia anterior (sweep)  
- Close > mínima (volta para dentro)  
- Candle anterior também estava “preso” abaixo  

**SHORT:** inverso no topo do range diário.

**Alvos:** R:R fixo **1:1,5** (`rr_ratio: 1.5`).

## Stop e alvo (correto para CRT+TBS)

| | Antes (errado) | Agora (correto) |
|--|----------------|-----------------|
| **Stop** | % fixo (0,6%) | **Abaixo/acima do wick do sweep** + buffer |
| **Alvo** | % fixo (0,9%) | **R:R 1:1,5** a partir do stop real, limitado ao extremo oposto do range CRT |

Parâmetros:
- `crt_stop_buffer_pct` — margem além do wick (0,05%)
- `crt_stop_max_pct` — teto se o sweep for muito largo
- `crt_alvo_extremo` — usa máxima/mínima do range CRT como teto do alvo

| Métrica | Resultado |
|---------|-----------|
| Retorno | **+14,4%** |
| Operações | **71** (~3/mês) |
| Taxa de acerto | **53,5%** |
| Profit factor | **1,72** |
| Max drawdown | 2,8% |
| R:R real | **1,49** (meta 1,5) |

Referência **diária** >> referência 4h nos testes.

## Comandos

```bash
python run.py -c config.crt-tbs.yaml backtest
python run.py -c config.crt-tbs.yaml simular-mes
python run.py -c config.fbs-crt-tbs.yaml paper --once
```

## Config

```yaml
estrategia: crt_tbs
crt_referencia: daily    # daily | 4h
rr_ratio: 1.5
stop_loss_pct: 0.006
```

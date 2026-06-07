# Stop dinâmico — agente protege lucro e reduz perda

## Ativação

```yaml
stop_dinamico: true
```

## Regras

### Proteger lucro

| Regra | Parâmetro | Ação |
|-------|-----------|------|
| **Breakeven** | `breakeven_apos_rr: 0.5` | Com +0,5R, stop vai para entrada |
| **Trailing** | `trailing_apos_rr: 1.0` | Com +1R, stop segue o preço (`trailing_dist_pct`) |

### Diminuir perda (memória adaptativa)

| Regra | Parâmetro | Ação |
|-------|-----------|------|
| **Confiança caiu** | `apertar_se_confianca_abaixo: 0.40` | Regime perdeu confiança → stop mais perto |
| **Perda parcial** | `apertar_perda_rr: -0.25` | Em -0,25R, reduz risco restante (`apertar_fator`) |
| **Tempo** | `apertar_apos_barras: 48` | 48 barras sem lucro → aperta stop |

## Motivos de saída no log

- `stop_be` — stop no breakeven
- `stop_trail` — trailing stop
- `stop_apertar` — agente apertou por memória/perda
- `stop_tempo` — apertou por tempo
- `target` — alvo normal

## Comandos

```bash
python run.py -c config.crt-tbs-dinamico.yaml backtest
python run.py -c config.crt-tbs-dinamico.yaml simular-mes
python run.py -c config.crt-tbs-dinamico.yaml simular-stop   # log de cada ajuste
```

Compare com `config.crt-tbs-fixo-12.yaml` (mesmo setup sem stop dinâmico).

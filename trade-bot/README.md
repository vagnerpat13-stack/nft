# Robô de Trade Adaptativo

Sistema de **backtest** com estratégia técnica (EMA + RSI), **gestão de risco** e **memória adaptativa** que penaliza padrões de mercado que geraram perdas e reforça os que geraram ganhos.

> **Aviso importante:** Nenhum robô garante “alta taxa de acerto” em mercado real. Resultados passados não garantem resultados futuros. Use primeiro em **backtest** e **paper trading**; opere com capital real apenas se entender os riscos e a regulamentação (CVM/B3 no Brasil).

## Como funciona a adaptação aos erros

1. Cada sinal é classificado em um **regime** (tendência, faixa de RSI, volatilidade, direção long/short).
2. Após cada operação fechada:
   - **Lucro** → aumenta a confiança daquele regime.
   - **Prejuízo** → reduz a confiança; sinais similares podem ser **bloqueados** até a confiança subir de novo.
3. Só entram operações com confiança acima de `confianca_minima` (configurável).

Isso reduz repetição de setups que falharam recentemente, sem prometer acerto constante.

## Instalação

```bash
cd trade-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso (backtest)

```bash
python run.py
python run.py --symbol VALE3.SA --period 1y
```

## Configuração (`config.yaml`)

| Parâmetro | Função |
|-----------|--------|
| `risco_por_operacao` | % do capital arriscado por trade |
| `stop_loss_pct` / `take_profit_pct` | Saídas automáticas |
| `penalidade_erro` / `bonus_acerto` | Velocidade da adaptação |
| `confianca_minima` | Filtro mínimo para abrir posição |
| `drawdown_max_pct` | Para o robô se o capital cair demais |

## Estrutura

```
trade-bot/
  config.yaml
  run.py
  src/
    adaptive.py    # Memória e aprendizado por regime
    strategy.py    # Sinais EMA + RSI
    risk.py        # Stop, target, tamanho de posição
    backtest.py    # Simulação histórica
    indicators.py
    data.py
```

## Próximos passos (você pode pedir)

- Integração com corretora (API) em modo **paper**
- Mais estratégias e otimização walk-forward
- Dashboard com métricas (Sharpe, expectancy)

## Relação com este repositório

O repositório principal é o agente **Professor de Matemática SEE/MG**. Este módulo `trade-bot/` foi adicionado como projeto separado para atender solicitação de automação de trade.

# Integração FBS + MetaTrader 5

A FBS não oferece API REST direta para o robô Python. A integração oficial é pelo **terminal MetaTrader 5** instalado no **Windows**, usando o pacote `MetaTrader5`.

## Requisitos

| Item | Detalhe |
|------|---------|
| Sistema | **Windows 10/11** (ou VPS Windows) |
| Terminal | [FBS MetaTrader 5](https://fbs.com/trading/metatrader5) instalado e **aberto** |
| Conta | Demo FBS para testes; Real só após validar |
| Python | 3.10+ no **mesmo PC** do MT5 |

> O pacote `MetaTrader5` **não funciona** em Linux/macOS nativamente. Use um PC ou VPS Windows com MT5 logado.

## Passo a passo

### 1. Instalar e logar na FBS

1. Baixe o **FBS MetaTrader 5** no site da FBS.
2. Abra o MT5 → **Arquivo → Conectar à conta de negociação**.
3. Anote:
   - **Login** (número da conta)
   - **Senha** (da conta de trading, não só do site)
   - **Servidor** (ex.: `FBS-Demo`, `FBS-Real`, `FBS-Real2` — copie exatamente da janela de login)

### 2. Habilitar negociação algorítmica

No MT5:

1. **Ferramentas → Opções → Expert Advisors**
2. Marque **Permitir negociação algorítmica**
3. Marque **Permitir importação de DLL** (se solicitado)
4. Clique em **OK**

### 3. Adicionar o símbolo

1. **Ctrl+U** (Observação de Mercado)
2. Encontre o par (ex.: `EURUSD`) → **Mostrar símbolo**
3. Abra um gráfico M5 do par

### 4. Instalar o robô Python

No PowerShell ou CMD, na pasta `trade-bot`:

```powershell
pip install -r requirements.txt
pip install -r requirements-mt5.txt
```

### 5. Configurar credenciais

Copie `.env.example` para `.env`:

```env
MT5_LOGIN=12345678
MT5_PASSWORD=sua_senha_trading
MT5_SERVER=FBS-Demo
# Opcional se o MT5 não estiver no caminho padrão:
# MT5_PATH=C:\Program Files\FBS MetaTrader 5\terminal64.exe
```

No Windows PowerShell:

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^([^#=]+)=(.*)$') { Set-Item -Path "env:$($matches[1])" -Value $matches[2] }
}
```

### 6. Testar conexão

Com o **MT5 aberto e logado**:

```powershell
python run.py mt5-test -c config.fbs.yaml
```

Deve mostrar login, servidor, saldo e cotação do símbolo.

### 7. Rodar em conta demo (paper real no MT5)

```powershell
python run.py paper -c config.fbs.yaml --once
python run.py paper -c config.fbs.yaml
```

O robô:

- Lê candles **do MT5** (não do yfinance)
- Envia ordens **market** com SL/TP definidos no `config`
- Usa volume em **lotes** (`mt5_lote: 0.01`)
- Só fecha posições com o mesmo `mt5_magic` (evita mexer em trades manuais)

## Arquivo `config.fbs.yaml`

Principais campos:

| Campo | Exemplo | Função |
|-------|---------|--------|
| `broker` | `mt5` | Ativa integração MT5 |
| `fonte_dados` | `mt5` | Candles do terminal |
| `symbol` / `mt5_symbol` | `EURUSD` | Nome igual ao MT5 |
| `mt5_lote` | `0.01` | Tamanho da posição em lotes |
| `mt5_server` | (ou env) | Servidor FBS exato |
| `paper_interval` | `5m` | Timeframe dos candles |

## Fluxo de arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Python (robô)  │────▶│  API MetaTrader5 │────▶│  FBS MT5    │
│  run.py paper   │     │  (biblioteca)    │     │  terminal   │
└─────────────────┘     └──────────────────┘     └─────────────┘
        │                                                │
        │  copy_rates / order_send                       │ ordens
        └────────────────────────────────────────────────┘
```

O terminal MT5 **precisa estar aberto** enquanto o robô roda.

## MetaTrader 4 (MT4)?

Este projeto usa **apenas MT5**. Se você usa MT4 na FBS:

- Migre para **MT5** (recomendado pela FBS), ou
- Use um Expert Advisor (MQL4) no gráfico que comunica com Python via arquivo/socket (não incluído aqui).

## Problemas comuns

| Erro | Solução |
|------|---------|
| `Falha ao conectar ao MetaTrader 5` | Abra o terminal FBS antes do `python run.py` |
| `Login MT5 falhou` | Confira login, senha e **nome exato** do servidor |
| `Símbolo não disponível` | Adicione o par na Observação de Mercado |
| `10030 Invalid fills` | Ajuste `mt5_desvio_pontos` ou tipo de filling (FBS) |
| Robô não abre ordem | Verifique “Negociação algorítmica” nas opções do MT5 |
| Linux / Mac | Rode em Windows ou VPS Windows com MT5 |

## Segurança

- Use **conta demo** até validar a estratégia.
- Não compartilhe `.env` com senha.
- `mt5_fechar_apenas_magic: true` evita fechar trades manuais seus.

## Comandos úteis

```powershell
python run.py mt5-test -c config.fbs.yaml
python run.py paper -c config.fbs.yaml --once
python run.py backtest --symbol EURUSD   # backtest ainda usa yfinance se não houver MT5
```

Para backtest histórico com dados idênticos ao MT5, rode o backtest no Windows com `fonte_dados: mt5` (futuro) ou exporte candles do MT5 para CSV.

# Agente Investimento B3

Agente de análise de investimentos na B3 baseado na **metodologia Logan**, combinando indicadores macroeconômicos do Banco Central do Brasil (BCB), screening fundamentalista de ações (`yfinance` com fallback para `brapi.dev`), leitura de carteira local (`portfolio.json`) e recomendação de aporte mensal.

## Arquitetura e arquivos principais

- [`run.sh`](run.sh) — entrypoint bash que cria `.venv` (se necessário), instala `requirements.txt` e imprime o relatório (`Macro`, `Top Candidatos`, `Sua Carteira` e `Recomendação do Mês`). Aceita o argumento opcional `demo`.
- [`scripts/macro.py`](scripts/macro.py) — consulta as séries públicas do SGS/BCB (`432` SELIC, `4389` CDI, `13522` IPCA 12m e `1` USD/BRL PTAX compra).
- [`scripts/screener.py`](scripts/screener.py) — aplica os filtros e a pontuação Logan sobre 47 ações (`DEFAULT_TICKERS`) ou sobre o subconjunto `DEMO_TICKERS` (`ITUB4`, `MGLU3`, `PETR4`, `VALE3`), verificando o segmento Novo Mercado (`NM`) na API pública da B3.
- [`scripts/brapi_client.py`](scripts/brapi_client.py) — cliente REST para `brapi.dev/api/quote/{ticker}` usado em modo `demo` ou fallback automático quando o Yahoo Finance está indisponível.
- [`portfolio.json`](portfolio.json) — estado local da carteira (`monthly_budget`, `currency`, `positions`).
- [`requirements.txt`](requirements.txt) — dependências Python (`yfinance==0.2.51`, `requests==2.32.3`, `pytest==8.3.5`).
- [`tests/`](tests/) — testes unitários com mocks (`test_macro.py`, `test_screener.py`, `test_brapi_client.py`).
- [`.claude/commands/morning-report.md`](.claude/commands/morning-report.md) — comando `/morning-report` para Claude Code Routine usando `WebFetch` nativo e a skill `/last30days`.
- [`.claude/skills/`](.claude/skills/) e [`skills-lock.json`](skills-lock.json) — skills `last30days` e `caveman*` (links simbólicos para `.agents/skills/`).
- [`docs/superpowers/`](docs/superpowers/) — especificação de design e plano de implementação originais.

## Metodologia Logan implementada (`scripts/screener.py`)

**Critérios eliminatórios:**
- Volume financeiro diário estimado (`avg_vol * price`) inferior a `R$ 10.000.000`.
- Quando há fundamentos disponíveis (`require_fundamentals=True`), menos de 2 períodos válidos de lucro líquido ou mais de 1 período com lucro líquido `<= 0` nos últimos 4 períodos.

**Pontuação (`0` a `4`), retornando os top 10 candidatos:**
- `+2`: empresa listada no **Novo Mercado** segundo a API da B3.
- `+1`: `Dívida / EBITDA < 2`.
- `+1`: *Earnings Yield* (`1 / P/L * 100`) superior à taxa do **CDI**.

## Pré-requisitos e configuração

- `Python 3.9+` e `bash`.
- Dependências instaláveis via `pip install -r requirements.txt` (ou automaticamente pelo [`run.sh`](run.sh)).

### `portfolio.json`

O repositório traz um arquivo inicial com carteira vazia e orçamento mensal de `R$ 1.000`:

```json
{
  "monthly_budget": 1000,
  "currency": "BRL",
  "positions": []
}
```

Cada item adicionado manualmente em `positions` deve conter `ticker`, `shares` e `avg_price` para exibição em `run.sh`.

### Variáveis de ambiente opcionais

| Variável | Padrão | Descrição |
| - | - | - |
| `DATA_PROVIDER` | `auto` | Provedor de dados do screener: `auto` (testa `yfinance` e faz fallback para `brapi`), `yfinance` ou `brapi`. |
| `BRAPI_TOKEN` | — | Token da `brapi.dev`. Sem token, o fallback `brapi` consulta apenas `PETR4`, `VALE3`, `ITUB4` e `MGLU3`. |
| `BRAPI_DELAY` | `0.2` | Pausa em segundos entre requisições à API da `brapi.dev`. |
| `YFINANCE_DELAY` | `0` | Pausa em segundos entre tickers no provedor `yfinance`. |

## Como executar

```bash
# Execução padrão (auto-detecção yfinance -> fallback brapi.dev)
./run.sh

# Modo demo (força brapi.dev nas 4 ações gratuitas: ITUB4, MGLU3, PETR4, VALE3)
./run.sh demo

# Screener completo via brapi.dev com token
BRAPI_TOKEN=seu_token ./run.sh
```

## Testes

```bash
python3 -m pytest tests/ -v
```

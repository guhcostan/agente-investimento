---
description: Relatório matinal de investimentos B3
---

Gere o relatório matinal de investimentos B3 usando WebFetch para buscar todos os dados. NÃO execute bash run.sh.

# Passo 1 — Leia a carteira local

Leia o arquivo `portfolio.json` e extraia `monthly_budget` e `positions`.

# Passo 2 — Busque dados macro via WebFetch

Faça WebFetch nestas URLs da API do Banco Central (BCB):

- SELIC: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json`
- CDI: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados/ultimos/1?formato=json`
- IPCA 12m: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados/ultimos/1?formato=json`
- USD/BRL: `https://query1.finance.yahoo.com/v8/finance/chart/USDBRL=X?interval=1d&range=1d`

Se alguma falhar, marque como ⚠️ indisponível e continue.

# Passo 3 — Screener Logan via WebFetch (Yahoo Finance)

Para cada ticker desta lista, faça WebFetch:
`https://query1.finance.yahoo.com/v10/finance/quoteSummary/{TICKER}.SA?modules=financialData,defaultKeyStatistics,incomeStatementHistory,price`

Tickers a avaliar:
WEGE3, ITUB4, BBAS3, RDOR3, PRIO3, EGIE3, TAEE11, TOTS3, RADL3, BBSE3, FLRY3, SMTO3, ITSA4, MDIA3, ENGI11, EQTL3, CPFE3, SBSP3, SUZB3, VALE3, PETR4, BPAC11, SLCE3, KLBN11, VIVT3

Para cada ticker, aplique os critérios Logan:

**Eliminatórios (qualquer um reprova):**
- Liquidez: `price.regularMarketVolume * price.regularMarketPrice < 10.000.000`
- Lucro recorrente: mais de 1 ano com Net Income negativo nos últimos 4 anos (`incomeStatementHistory`)

**Score 0-4 (aprovados nos eliminatórios):**
1. +2 se governança Novo Mercado (verifique se `price.exchange` == "SAO" e `defaultKeyStatistics` indica NM — use seu conhecimento: WEGE3, RDOR3, TOTS3, RADL3, FLRY3, SMTO3, MDIA3, EQTL3, SBSP3, VIVT3, BPAC11, SLCE3 são Novo Mercado)
2. +1 se D/EBITDA < 2x (`financialData.totalDebt / financialData.ebitda`)
3. +1 se Earnings Yield > CDI (`1 / defaultKeyStatistics.trailingPE * 100 > CDI%`)

Ordene por score decrescente. Mantenha top 5.

# Passo 4 — Notícias dos top 3 candidatos

Para cada um dos 3 primeiros candidatos do ranking, execute `/last30days {TICKER} ações B3 investimento`.

# Passo 5 — Monte o relatório final

```
# Relatório Matinal — {data de hoje}

## Macro
SELIC: X% | CDI: X% | IPCA 12m: X% | USD/BRL: R$X,XX

## Top Candidatos (Metodologia Logan)
1. TICKER — Score X/4 — R$XX,XX
   • critérios aprovados

## Notícias (últimos 30 dias)
### TICKER1
[destaques do last30days]

### TICKER2
[destaques do last30days]

### TICKER3
[destaques do last30days]

## Sua Carteira
[posições ou "Carteira vazia — primeiro aporte"]

## Recomendação do Mês
Com R$X.000: compre **X ações de TICKER** @ R$XX,XX
Score Logan: X/4
• justificativa fundamentalista
```

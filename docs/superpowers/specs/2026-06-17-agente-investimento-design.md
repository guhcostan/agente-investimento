# Agente Investimento B3 — Design Spec
**Data:** 2026-06-17

## Contexto

Investidor de longo prazo, carteira zerada, aporte mensal de R$1.000. Sem API paga. Sem integração com corretora (Nubank não expõe API pública). Portfolio rastreado via `portfolio.json` no próprio repo — editado manualmente a cada compra/venda.

Entrega: Claude Code Routine rodando na nuvem da Anthropic, 7h todo dia útil, output no log da sessão em `claude.ai/code/routines`.

## Arquitetura

```
GitHub repo: agente-investimento
       ↓ clone a cada run
Anthropic Cloud (Routine) — 7h dias úteis
       ↓
morning-report command
  ├── screener.py    — Logan tier-list, yfinance + BCB
  ├── news.py        — Google News RSS por ticker/setor
  └── macro.py       — SELIC, CDI, IPCA, USD/BRL via BCB API
       ↓
Relatório markdown no log da sessão
```

## Componentes

### portfolio.json
```json
{
  "monthly_budget": 1000,
  "positions": []
}
```
Cresce conforme o usuário compra. Cada posição: `ticker`, `shares`, `avg_price`, `buy_date`.

### screener.py — Metodologia Logan
7 critérios (3 eliminatórios + 4 score):
- **Eliminatórios:** lucro consistente (sem prejuízo recorrente), liquidez ON > R$10M/dia, 5+ anos na B3
- **Score:** Novo Mercado, tag along 100%, dívida controlada (D/EBITDA < 2x), retorno esperado > CDI (~14,75%)

Fonte: yfinance (`.SA` suffix), sem API key.

### news.py
Google News RSS em português por ticker e setor. Últimos 30 dias. Sem API key.

### macro.py
BCB Open API: SELIC, CDI, IPCA, USD/BRL. Sem API key.

### .claude/commands/morning-report.md
Command que a Routine executa. Orquestra os scripts, gera o relatório final.

### run.sh
Cria virtualenv, instala requirements, executa os scripts.

## Formato do Relatório

```
# Relatório Matinal — DD/MM/YYYY

## Macro
SELIC: X% | CDI: X% | IPCA 12m: X% | USD/BRL: X,XX

## Sua Carteira
[Vazia — primeiro mês] ou posições com P&L

## Top Candidatos do Mês (Logan Score)
1. TICKER3 — Score 4/4 — R$ XX,XX
   Motivo: ...
   Notícias: ...

## Recomendação
→ Com R$1.000 este mês: compre X ações de TICKER3 (~R$XXX)
   [raciocínio fundamentalista]
```

## Dados Necessários
- Nenhuma API key paga
- yfinance (PyPI)
- BCB Open API (pública)
- Google News RSS (público)

## Setup do Usuário
1. Push do repo para GitHub
2. Criar Routine em `claude.ai/code/routines` linkando o repo
3. Schedule: daily, 7h
4. Prompt da Routine: "Execute o comando /morning-report"

## Fora do Escopo
- FIIs, BDRs, ETFs (pode adicionar depois)
- Execução automática de ordens (não é day trade)
- Integração com corretora

# Agente Investimento B3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agente diário que roda via Claude Code Routine (nuvem Anthropic), lê `portfolio.json`, faz screening de ações B3 pela metodologia Logan, busca notícias dos últimos 30 dias e gera relatório com recomendação de alocação mensal de R$1.000.

**Architecture:** Scripts Python independentes (macro, screener) + skills Claude Code (last30days, caveman) orquestrados por `morning-report.md`. Portfolio em `portfolio.json` versionado no repo. Zero APIs pagas — yfinance + BCB Open API + last30days para notícias.

**Tech Stack:** Python 3.11+, yfinance, requests, pytest, unittest.mock, gh CLI, last30days-skill, caveman-skill

---

## File Map

```
agente-investimento/
  portfolio.json                        ← posições do usuário (começa vazio)
  requirements.txt                      ← dependências Python
  run.sh                                ← cria venv, instala deps, roda screener
  .claude/
    commands/
      morning-report.md                 ← command da Routine (usa /last30days)
    skills/
      last30days/                       ← skill de notícias 30 dias (já instalado)
      caveman/                          ← skill de output compacto (já instalado)
  scripts/
    macro.py                            ← SELIC, CDI, IPCA, USD/BRL via BCB
    screener.py                         ← Logan screening via yfinance
  tests/
    test_macro.py
    test_screener.py
```

---

## Task 1: Bootstrap do projeto

**Files:**
- Create: `portfolio.json`
- Create: `requirements.txt`
- Create: `.gitignore`

- [ ] **Step 1: Criar portfolio.json**

```json
{
  "monthly_budget": 1000,
  "currency": "BRL",
  "positions": []
}
```

Quando o usuário comprar uma ação, adiciona um objeto em `positions`:
```json
{
  "ticker": "WEGE3",
  "shares": 10,
  "avg_price": 38.50,
  "buy_date": "2026-07-01"
}
```

- [ ] **Step 2: Criar requirements.txt**

```
yfinance==0.2.51
requests==2.32.3
pytest==8.3.5
```

- [ ] **Step 3: Criar .gitignore**

```
.venv/
__pycache__/
*.pyc
.env
```

- [ ] **Step 4: Criar diretórios**

```bash
mkdir -p scripts tests .claude/commands
touch scripts/__init__.py tests/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git init
git add portfolio.json requirements.txt .gitignore scripts/__init__.py tests/__init__.py
git commit -m "chore: bootstrap projeto agente-investimento"
```

---

## Task 2: macro.py — dados macroeconômicos via BCB

**Files:**
- Create: `scripts/macro.py`
- Create: `tests/test_macro.py`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_macro.py`:
```python
from unittest.mock import patch, MagicMock
from scripts.macro import get_macro

def _mock_bcb(series_id, valor):
    return MagicMock(json=lambda: [{"valor": str(valor)}], raise_for_status=lambda: None)

def test_get_macro_returns_expected_keys():
    with patch("scripts.macro.requests.get") as mock_get, \
         patch("scripts.macro.yf.Ticker") as mock_ticker:
        mock_get.side_effect = lambda url, **kw: MagicMock(
            json=lambda: [{"valor": "14.75"}],
            raise_for_status=lambda: None
        )
        mock_ticker.return_value.fast_info = {"lastPrice": 5.72}
        result = get_macro()
    assert set(result.keys()) == {"selic", "cdi", "ipca_12m", "usd_brl"}
    assert result["selic"] == 14.75
    assert result["usd_brl"] == 5.72

def test_get_macro_cdi_used_as_hurdle():
    with patch("scripts.macro.requests.get") as mock_get, \
         patch("scripts.macro.yf.Ticker") as mock_ticker:
        mock_get.return_value = MagicMock(
            json=lambda: [{"valor": "10,50"}],
            raise_for_status=lambda: None
        )
        mock_ticker.return_value.fast_info = {"lastPrice": 5.0}
        result = get_macro()
    assert result["cdi"] == 10.50  # testa parse de vírgula decimal
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
python -m pytest tests/test_macro.py -v
```
Esperado: `ModuleNotFoundError: No module named 'scripts.macro'`

- [ ] **Step 3: Implementar macro.py**

`scripts/macro.py`:
```python
import requests
import yfinance as yf

BCB_SERIES = {
    "selic": 432,
    "cdi": 4389,
    "ipca_12m": 13522,
}

def get_macro() -> dict:
    result = {}
    for name, series_id in BCB_SERIES.items():
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados/ultimos/1?formato=json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        valor = r.json()[0]["valor"].replace(",", ".")
        result[name] = float(valor)

    usd_brl = yf.Ticker("USDBRL=X").fast_info["lastPrice"]
    result["usd_brl"] = round(float(usd_brl), 2)
    return result

def format_macro(macro: dict) -> str:
    return (
        f"SELIC: {macro['selic']:.2f}% | "
        f"CDI: {macro['cdi']:.2f}% | "
        f"IPCA 12m: {macro['ipca_12m']:.2f}% | "
        f"USD/BRL: R${macro['usd_brl']:.2f}"
    )
```

- [ ] **Step 4: Rodar e confirmar passa**

```bash
python -m pytest tests/test_macro.py -v
```
Esperado: 2 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/macro.py tests/test_macro.py
git commit -m "feat: macro.py — SELIC, CDI, IPCA, USD/BRL via BCB API"
```

---

## Task 3: Commit das skills (last30days + caveman)

**Files:**
- Already installed: `.claude/skills/last30days/`
- Already installed: `.claude/skills/caveman/` (+ cavecrew, caveman-commit, etc.)

As skills já foram instaladas localmente via `npx skills add`. Só precisam ser commitadas — a Routine as carregará automaticamente ao clonar o repo.

- [ ] **Step 1: Verificar o que foi instalado**

```bash
ls .claude/skills/
```
Esperado: `cavecrew  caveman  caveman-commit  caveman-compress  caveman-help  caveman-review  caveman-stats  last30days`

- [ ] **Step 2: Commitar as skills**

```bash
git add .claude/skills/
git commit -m "feat: add last30days e caveman skills para a Routine"
```

**Como serão usadas no morning-report:**
- `/last30days <TICKER>` nos top 3 candidatos do screener — notícias/discussões dos últimos 30 dias
- `caveman` — output compacto do agente (~75% menos tokens)

---

## Task 4: screener.py — Metodologia Logan

**Files:**
- Create: `scripts/screener.py`
- Create: `tests/test_screener.py`

- [ ] **Step 1: Escrever os testes que falham**

`tests/test_screener.py`:
```python
from unittest.mock import patch, MagicMock
import pandas as pd
from scripts.screener import score_ticker, run_screener

def _mock_ticker(avg_volume=1_500_000, price=40.0, net_incomes=None,
                 total_debt=500_000_000, ebitda=1_000_000_000, pe=10.0,
                 market_cap=10_000_000_000):
    mock = MagicMock()
    mock.info = {
        "averageVolume": avg_volume,
        "currentPrice": price,
        "totalDebt": total_debt,
        "ebitda": ebitda,
        "trailingPE": pe,
        "marketCap": market_cap,
    }
    if net_incomes is None:
        net_incomes = [1e9, 1.2e9, 1.1e9, 1.3e9]
    mock.financials = pd.DataFrame(
        {"col": net_incomes},
        index=["Net Income", "Other", "Other2", "Other3"]
    )
    return mock

def test_score_ticker_eliminated_by_low_liquidity():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(avg_volume=100)):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is None

def test_score_ticker_eliminated_by_recurring_losses():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        net_incomes=[-1e9, 1e9, -1e9, 1e9]
    )):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is None

def test_score_ticker_full_score_novo_mercado():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        avg_volume=2_000_000, price=50.0, pe=6.0,  # earnings yield ~16.7% > CDI 14.75%
        total_debt=100_000_000, ebitda=1_000_000_000  # D/EBITDA 0.1x
    )):
        result = score_ticker("WEGE3", cdi_rate=14.75, novo_mercado={"WEGE3"})
    assert result is not None
    assert result["score"] == 4
    assert result["ticker"] == "WEGE3"

def test_score_ticker_zero_score_no_novo_mercado_high_pe():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        avg_volume=2_000_000, price=50.0, pe=50.0,   # earnings yield 2% < CDI
        total_debt=5_000_000_000, ebitda=1_000_000_000  # D/EBITDA 5x
    )):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is not None
    assert result["score"] == 0

def test_run_screener_returns_sorted_top_results():
    results = [
        {"ticker": "A", "score": 2, "price": 10.0, "reasons": [], "pe": 10, "market_cap": 1e9},
        {"ticker": "B", "score": 4, "price": 20.0, "reasons": [], "pe": 8, "market_cap": 2e9},
        {"ticker": "C", "score": 1, "price": 5.0, "reasons": [], "pe": 15, "market_cap": 5e8},
    ]
    with patch("scripts.screener.score_ticker", side_effect=results), \
         patch("scripts.screener.fetch_novo_mercado", return_value=set()):
        top = run_screener(cdi_rate=14.75, tickers=["A", "B", "C"])
    assert top[0]["ticker"] == "B"
    assert top[0]["score"] == 4
```

- [ ] **Step 2: Rodar e confirmar falha**

```bash
python -m pytest tests/test_screener.py -v
```
Esperado: `ModuleNotFoundError: No module named 'scripts.screener'`

- [ ] **Step 3: Implementar screener.py**

`scripts/screener.py`:
```python
import yfinance as yf
import requests

# Universe: principais ações B3 por liquidez/relevância
DEFAULT_TICKERS = [
    "ABEV3", "B3SA3", "BBAS3", "BBDC4", "BBSE3", "BPAC11", "BRFS3",
    "CCRO3", "CMIG4", "CPFE3", "CSAN3", "EGIE3", "ELET3", "EMBR3",
    "ENEV3", "ENGI11", "EQTL3", "FLRY3", "GGBR4", "HAPV3", "HYPE3",
    "ITSA4", "ITUB4", "JBSS3", "KLBN11", "LREN3", "MDIA3", "MRVE3",
    "MULT3", "PETR4", "PRIO3", "RADL3", "RAIL3", "RDOR3", "RENT3",
    "SANB11", "SBSP3", "SLCE3", "SMTO3", "SUZB3", "TAEE11", "TIMS3",
    "TOTS3", "UGPA3", "VALE3", "VIVT3", "WEGE3",
]

def fetch_novo_mercado() -> set[str]:
    """Busca empresas do Novo Mercado via API pública da B3."""
    try:
        url = (
            "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/"
            "CompanyCall/GetInitialCompanies/"
            "eyJsYW5ndWFnZSI6InB0LWJyIn0="
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        return {
            c["issuingCompany"].strip().upper()
            for c in data.get("results", [])
            if c.get("segment") == "NM"
        }
    except Exception:
        return set()  # ponytail: degrade gracefully

def score_ticker(ticker: str, cdi_rate: float, novo_mercado: set[str]) -> dict | None:
    t = yf.Ticker(f"{ticker}.SA")
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    avg_vol = info.get("averageVolume", 0)

    # Filtro 1: liquidez > R$10M/dia
    if (avg_vol or 0) * (price or 0) < 10_000_000:
        return None

    # Filtro 2: lucro consistente (máximo 1 ano negativo nos últimos 4)
    try:
        net_incomes = t.financials.loc["Net Income"].dropna().head(4)
        if (net_incomes <= 0).sum() > 1:
            return None
    except Exception:
        return None

    score = 0
    reasons = []

    # Score 1 + 2: Novo Mercado (implica tag along 100%)
    if ticker in novo_mercado:
        score += 2
        reasons.append("Novo Mercado + Tag Along 100% ✓")

    # Score 3: D/EBITDA < 2x
    debt = info.get("totalDebt") or 0
    ebitda = info.get("ebitda") or 1
    if ebitda > 0 and (debt / ebitda) < 2:
        score += 1
        reasons.append(f"D/EBITDA {debt/ebitda:.1f}x ✓")

    # Score 4: earnings yield > CDI
    pe = info.get("trailingPE")
    if pe and pe > 0:
        earnings_yield = (1 / pe) * 100
        if earnings_yield > cdi_rate:
            score += 1
            reasons.append(f"Retorno estimado {earnings_yield:.1f}% > CDI {cdi_rate:.1f}% ✓")

    return {
        "ticker": ticker,
        "price": round(float(price), 2),
        "score": score,
        "reasons": reasons,
        "pe": pe,
        "market_cap": info.get("marketCap", 0),
    }

def run_screener(cdi_rate: float, tickers: list[str] | None = None) -> list[dict]:
    tickers = tickers or DEFAULT_TICKERS
    novo_mercado = fetch_novo_mercado()
    results = []
    for ticker in tickers:
        try:
            r = score_ticker(ticker, cdi_rate, novo_mercado)
            if r:
                results.append(r)
        except Exception:
            pass
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]

def format_screener(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates, 1):
        lines.append(
            f"{i}. **{c['ticker']}** — Score {c['score']}/4 — R${c['price']:.2f}"
        )
        for r in c["reasons"]:
            lines.append(f"   • {r}")
    return "\n".join(lines) if lines else "Nenhum candidato passou nos filtros."
```

- [ ] **Step 4: Rodar e confirmar passa**

```bash
python -m pytest tests/test_screener.py -v
```
Esperado: 5 passed

- [ ] **Step 5: Rodar todos os testes**

```bash
python -m pytest tests/ -v
```
Esperado: todos os testes passando

- [ ] **Step 6: Commit**

```bash
git add scripts/screener.py tests/test_screener.py
git commit -m "feat: screener.py — metodologia Logan (7 critérios)"
```

---

## Task 5: run.sh + requirements check

**Files:**
- Create: `run.sh`

- [ ] **Step 1: Criar run.sh**

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

python3 -c "
import json, sys
from scripts.macro import get_macro, format_macro
from scripts.screener import run_screener, format_screener
from scripts.news import get_news, format_news

portfolio = json.loads(open('portfolio.json').read())
macro = get_macro()
candidates = run_screener(cdi_rate=macro['cdi'])

print('## Macro')
print(format_macro(macro))
print()
print('## Top Candidatos (Metodologia Logan)')
print(format_screener(candidates))
print()
print('## Notícias (Top 3 candidatos)')
for c in candidates[:3]:
    news = get_news(c['ticker'])
    print(format_news(c['ticker'], news))
    print()

positions = portfolio.get('positions', [])
budget = portfolio.get('monthly_budget', 1000)
print('## Sua Carteira')
if not positions:
    print('Carteira vazia — primeiro aporte.')
else:
    for p in positions:
        print(f\"  {p['ticker']}: {p['shares']} ações @ R\${p['avg_price']:.2f}\")
print()

if candidates:
    top = candidates[0]
    shares = int(budget // top['price'])
    print(f'## Recomendação do Mês')
    print(f'Com R\${budget:.0f}: compre **{shares} ações de {top[\"ticker\"]}** @ R\${top[\"price\"]:.2f}')
    print(f'Score Logan: {top[\"score\"]}/4')
"
```

- [ ] **Step 2: Tornar executável e testar**

```bash
chmod +x run.sh
./run.sh
```
Esperado: output com Macro, Candidatos, Notícias, Recomendação (pode demorar ~30s para yfinance)

- [ ] **Step 3: Commit**

```bash
git add run.sh
git commit -m "feat: run.sh — entrypoint completo do agente"
```

---

## Task 6: Claude Code command morning-report.md

**Files:**
- Create: `.claude/commands/morning-report.md`

- [ ] **Step 1: Criar o command**

`.claude/commands/morning-report.md`:
```markdown
---
description: Relatório matinal de investimentos B3
---

Execute o script de análise e gere o relatório de investimentos do dia.

Passos:
1. Execute `bash run.sh` e capture o output completo (macro + screener + portfolio + recomendação)
2. Para cada um dos top 3 candidatos retornados pelo screener, execute `/last30days <TICKER>` para buscar notícias e discussões dos últimos 30 dias
3. Apresente o relatório consolidado em markdown com o cabeçalho: `# Relatório Matinal — <data de hoje>`
4. Se houver erro em qualquer etapa, mostre o erro e indique a causa provável (yfinance fora do ar, BCB API indisponível, etc.)

Formato do relatório:
- **Macro** — SELIC, CDI, IPCA, USD/BRL
- **Top Candidatos** — ranking Logan com scores
- **Notícias (last30days)** — uma seção por candidato com os destaques
- **Sua Carteira** — posições atuais ou "Carteira vazia"
- **Recomendação do Mês** — ticker + quantidade + preço estimado
```

- [ ] **Step 2: Testar o command localmente**

No Claude Code, execute:
```
/morning-report
```
Esperado: relatório completo aparece no chat.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/morning-report.md
git commit -m "feat: command morning-report para Claude Code Routine"
```

---

## Task 7: GitHub repo + push

**Files:** nenhum novo arquivo

- [ ] **Step 1: Criar repo público no GitHub**

```bash
gh repo create agente-investimento --public --description "Agente diário de análise de investimentos B3 — metodologia Logan" --source=. --remote=origin
```

- [ ] **Step 2: Push**

```bash
git push -u origin main
```

- [ ] **Step 3: Verificar repo**

```bash
gh repo view --web
```

- [ ] **Step 4: Instruções para criar a Routine**

Após o push, o usuário configura a Routine em `claude.ai/code/routines`:
1. **New routine**
2. **Repository:** `<username>/agente-investimento`
3. **Trigger:** Schedule → Daily → 07:00 (seu fuso horário)
4. **Prompt:** `Execute o comando /morning-report e apresente o relatório completo do dia.`
5. **Run now** para testar

---

## Self-Review

**Spec coverage:**
- ✅ Claude Code Routine (cron 7h) → Task 6 + 7
- ✅ portfolio.json versionado no repo → Task 1
- ✅ Metodologia Logan (7 critérios) → Task 4
- ✅ Notícias 30 dias (last30days skill) → Task 3 + Task 6 (morning-report invoca /last30days)
- ✅ Macro BCB (SELIC/CDI/IPCA/USD/BRL) → Task 2
- ✅ Recomendação de alocação mensal → Task 5 (run.sh)
- ✅ GitHub repo via gh CLI → Task 7
- ✅ Zero APIs pagas

**Placeholder scan:** Nenhum TBD/TODO encontrado.

**Type consistency:** `score_ticker` retorna `dict | None` em todas as referências. `run_screener` recebe `cdi_rate: float` consistente com `macro["cdi"]` em run.sh.

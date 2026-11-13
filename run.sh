#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-}"
if [ "$MODE" = "demo" ]; then
  export DATA_PROVIDER=brapi
fi

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

python3 - <<EOF
import json
import os
from scripts.macro import get_macro, format_macro
from scripts.screener import (
    DEMO_TICKERS, resolve_provider, run_screener, format_screener,
)

mode = "${MODE}"
portfolio = json.loads(open("portfolio.json").read())
positions = portfolio.get("positions", [])
budget = portfolio.get("monthly_budget", 1000)

macro = None
candidates = []
provider_note = ""

try:
    macro = get_macro()
    print("## Macro")
    print(format_macro(macro))
except Exception as e:
    print(f"## Macro\n⚠️ Indisponível: {e}")
print()

try:
    cdi = macro["cdi"] if macro else 14.75
    provider = resolve_provider()
    tickers = DEMO_TICKERS if mode == "demo" else None

    if mode == "demo":
        provider_note = (
            f"ℹ️ Modo demo (brapi.dev) — {len(DEMO_TICKERS)} ações de teste. "
            "Para screener completo: BRAPI_TOKEN=... ./run.sh"
        )
    elif provider == "brapi" and not os.environ.get("BRAPI_TOKEN"):
        provider_note = (
            "ℹ️ Yahoo Finance indisponível — usando brapi.dev (4 ações de teste). "
            "Defina BRAPI_TOKEN para o universo completo."
        )
        tickers = DEMO_TICKERS
    elif provider == "brapi" and os.environ.get("BRAPI_TOKEN"):
        provider_note = (
            "ℹ️ Plano brapi free: cotação completa em ~47 ações; "
            "fundamentos só em PETR4/VALE3/ITUB4/MGLU3."
        )

    candidates = run_screener(cdi_rate=cdi, tickers=tickers, provider=provider)
    print("## Top Candidatos (Metodologia Logan)")
    print(format_screener(candidates, provider_note))
except Exception as e:
    print(f"## Top Candidatos\n⚠️ Indisponível: {e}")
print()

print("## Sua Carteira")
if not positions:
    print("Carteira vazia — primeiro aporte.")
else:
    for p in positions:
        print(f"  {p['ticker']}: {p['shares']} ações @ R\${p['avg_price']:.2f}")
print()

if candidates:
    top = candidates[0]
    shares = int(budget // top["price"])
    print("## Recomendação do Mês")
    print(f"Com R\${budget:.0f}: compre **{shares} ações de {top['ticker']}** @ R\${top['price']:.2f}")
    print(f"Score Logan: {top['score']}/4")
    for r in top["reasons"]:
        print(f"  • {r}")
EOF

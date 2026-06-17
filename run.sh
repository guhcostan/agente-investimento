#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

python3 - <<'EOF'
import json
from scripts.macro import get_macro, format_macro
from scripts.screener import run_screener, format_screener

portfolio = json.loads(open("portfolio.json").read())
positions = portfolio.get("positions", [])
budget = portfolio.get("monthly_budget", 1000)

macro = None
candidates = []

try:
    macro = get_macro()
    print("## Macro")
    print(format_macro(macro))
except Exception as e:
    print(f"## Macro\n⚠️ Indisponível: {e}")
print()

try:
    cdi = macro["cdi"] if macro else 14.75  # fallback CDI estimado
    candidates = run_screener(cdi_rate=cdi)
    print("## Top Candidatos (Metodologia Logan)")
    print(format_screener(candidates))
except Exception as e:
    print(f"## Top Candidatos\n⚠️ Indisponível: {e}")
print()

print("## Sua Carteira")
if not positions:
    print("Carteira vazia — primeiro aporte.")
else:
    for p in positions:
        print(f"  {p['ticker']}: {p['shares']} ações @ R${p['avg_price']:.2f}")
print()

if candidates:
    top = candidates[0]
    shares = int(budget // top["price"])
    print("## Recomendação do Mês")
    print(f"Com R${budget:.0f}: compre **{shares} ações de {top['ticker']}** @ R${top['price']:.2f}")
    print(f"Score Logan: {top['score']}/4")
    for r in top["reasons"]:
        print(f"  • {r}")
EOF

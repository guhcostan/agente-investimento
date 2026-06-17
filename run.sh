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
macro = get_macro()
candidates = run_screener(cdi_rate=macro["cdi"])

print("## Macro")
print(format_macro(macro))
print()

print("## Top Candidatos (Metodologia Logan)")
print(format_screener(candidates))
print()

positions = portfolio.get("positions", [])
budget = portfolio.get("monthly_budget", 1000)

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

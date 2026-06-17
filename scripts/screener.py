import yfinance as yf
import requests

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
        return set()  # ponytail: degrade gracefully if B3 API is down


def score_ticker(ticker: str, cdi_rate: float, novo_mercado: set[str]) -> dict | None:
    t = yf.Ticker(f"{ticker}.SA")
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    avg_vol = info.get("averageVolume", 0)

    # Filtro 1: liquidez > R$10M/dia
    if (avg_vol or 0) * (price or 0) < 10_000_000:
        return None

    # Filtro 2: lucro consistente (máx 1 ano negativo nos últimos 4)
    try:
        net_incomes = t.financials.loc["Net Income"].dropna().head(4)
        if (net_incomes <= 0).sum() > 1:
            return None
    except Exception:
        return None

    score = 0
    reasons = []

    # Score 1+2: Novo Mercado implica tag along 100%
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
    if not candidates:
        return "Nenhum candidato passou nos filtros."
    lines = []
    for i, c in enumerate(candidates, 1):
        lines.append(f"{i}. **{c['ticker']}** — Score {c['score']}/4 — R${c['price']:.2f}")
        for r in c["reasons"]:
            lines.append(f"   • {r}")
    return "\n".join(lines)

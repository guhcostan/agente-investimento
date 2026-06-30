import os
import time

import requests
import yfinance as yf

from scripts.brapi_client import BRAPI_FREE_TICKERS, fetch_quotes

DEFAULT_TICKERS = [
    "ABEV3", "B3SA3", "BBAS3", "BBDC4", "BBSE3", "BPAC11", "BRFS3",
    "CCRO3", "CMIG4", "CPFE3", "CSAN3", "EGIE3", "ELET3", "EMBR3",
    "ENEV3", "ENGI11", "EQTL3", "FLRY3", "GGBR4", "HAPV3", "HYPE3",
    "ITSA4", "ITUB4", "JBSS3", "KLBN11", "LREN3", "MDIA3", "MRVE3",
    "MULT3", "PETR4", "PRIO3", "RADL3", "RAIL3", "RDOR3", "RENT3",
    "SANB11", "SBSP3", "SLCE3", "SMTO3", "SUZB3", "TAEE11", "TIMS3",
    "TOTS3", "UGPA3", "VALE3", "VIVT3", "WEGE3",
]

DEMO_TICKERS = sorted(BRAPI_FREE_TICKERS)


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


def _score_from_data(
    ticker: str,
    price: float,
    avg_vol: float,
    net_incomes: list[float],
    debt_ebitda: float | None,
    pe: float | None,
    cdi_rate: float,
    novo_mercado: set[str],
    market_cap: float = 0,
) -> dict | None:
    if (avg_vol or 0) * (price or 0) < 10_000_000:
        return None

    valid = [n for n in net_incomes if n is not None]
    if len(valid) < 2 or sum(1 for n in valid[:4] if n <= 0) > 1:
        return None

    score = 0
    reasons = []

    if ticker in novo_mercado:
        score += 2
        reasons.append("Novo Mercado + Tag Along 100% ✓")

    if debt_ebitda is not None and debt_ebitda < 2:
        score += 1
        reasons.append(f"D/EBITDA {debt_ebitda:.1f}x ✓")

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
        "market_cap": market_cap,
    }


def score_ticker(ticker: str, cdi_rate: float, novo_mercado: set[str]) -> dict | None:
    t = yf.Ticker(f"{ticker}.SA")
    info = t.info

    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    avg_vol = info.get("averageVolume", 0)

    try:
        net_incomes = t.financials.loc["Net Income"].dropna().head(4).tolist()
    except Exception:
        return None

    debt = info.get("totalDebt") or 0
    ebitda = info.get("ebitda") or 1
    debt_ebitda = (debt / ebitda) if ebitda > 0 else None
    pe = info.get("trailingPE")

    return _score_from_data(
        ticker, price, avg_vol, net_incomes, debt_ebitda, pe,
        cdi_rate, novo_mercado, info.get("marketCap", 0),
    )


def score_ticker_brapi(quote: dict, cdi_rate: float, novo_mercado: set[str]) -> dict | None:
    price = quote.get("regularMarketPrice") or 0
    avg_vol = quote.get("regularMarketVolume") or 0

    net_incomes = [
        row.get("netIncome")
        for row in (quote.get("incomeStatementHistory") or [])[:4]
    ]

    stats = quote.get("defaultKeyStatistics") or {}
    debt = stats.get("totalDebt")
    ebitda = stats.get("ebitda")
    if debt and ebitda and ebitda > 0:
        debt_ebitda = debt / ebitda
    else:
        debt_ebitda = stats.get("enterpriseToEbitda")

    pe = quote.get("priceEarnings") or stats.get("trailingPE")
    ticker = (quote.get("symbol") or "").upper()

    return _score_from_data(
        ticker, price, avg_vol, net_incomes, debt_ebitda, pe,
        cdi_rate, novo_mercado, quote.get("marketCap", 0),
    )


def yfinance_available() -> bool:
    try:
        info = yf.Ticker("PETR4.SA").info
        return bool(info.get("currentPrice") or info.get("regularMarketPrice"))
    except Exception:
        return False


def resolve_provider(explicit: str | None = None) -> str:
    provider = (explicit or os.environ.get("DATA_PROVIDER", "auto")).lower()
    if provider == "auto":
        return "brapi" if not yfinance_available() else "yfinance"
    return provider


def run_screener(
    cdi_rate: float,
    tickers: list[str] | None = None,
    provider: str | None = None,
) -> list[dict]:
    tickers = tickers or DEFAULT_TICKERS
    resolved = resolve_provider(provider)
    novo_mercado = fetch_novo_mercado()

    if resolved == "brapi":
        return _run_screener_brapi(cdi_rate, tickers, novo_mercado)
    return _run_screener_yfinance(cdi_rate, tickers, novo_mercado)


def _run_screener_yfinance(
    cdi_rate: float, tickers: list[str], novo_mercado: set[str],
) -> list[dict]:
    results = []
    for ticker in tickers:
        try:
            r = score_ticker(ticker, cdi_rate, novo_mercado)
            if r:
                results.append(r)
        except Exception:
            pass
        time.sleep(float(os.environ.get("YFINANCE_DELAY", "0")))
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]


def _run_screener_brapi(
    cdi_rate: float, tickers: list[str], novo_mercado: set[str],
) -> list[dict]:
    quotes = fetch_quotes(tickers)
    results = []
    for ticker in tickers:
        quote = quotes.get(ticker.upper())
        if not quote:
            continue
        try:
            r = score_ticker_brapi(quote, cdi_rate, novo_mercado)
            if r:
                results.append(r)
        except Exception:
            pass
    return sorted(results, key=lambda x: x["score"], reverse=True)[:10]


def format_screener(candidates: list[dict], provider_note: str = "") -> str:
    if not candidates:
        msg = "Nenhum candidato passou nos filtros."
        return f"{msg}\n{provider_note}" if provider_note else msg
    lines = []
    if provider_note:
        lines.append(provider_note)
    for i, c in enumerate(candidates, 1):
        lines.append(f"{i}. **{c['ticker']}** — Score {c['score']}/4 — R${c['price']:.2f}")
        for r in c["reasons"]:
            lines.append(f"   • {r}")
    return "\n".join(lines)

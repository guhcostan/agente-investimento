import os
import time

import requests

BRAPI_BASE = "https://brapi.dev/api"
BRAPI_FREE_TICKERS = {"PETR4", "VALE3", "ITUB4", "MGLU3"}
BRAPI_MODULES = "incomeStatementHistory,defaultKeyStatistics"


def get_token() -> str | None:
    return os.environ.get("BRAPI_TOKEN") or None


def _fetch_one(ticker: str, token: str | None, modules: bool) -> dict | None:
    url = f"{BRAPI_BASE}/quote/{ticker}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"modules": BRAPI_MODULES} if modules else {}
    r = requests.get(url, params=params, headers=headers, timeout=30)
    if r.status_code in (403, 400) and modules:
        r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0] if results else None


def fetch_quotes(tickers: list[str], token: str | None = None) -> dict[str, dict]:
    token = token if token is not None else get_token()
    if not token:
        tickers = [t for t in tickers if t in BRAPI_FREE_TICKERS]

    quotes: dict[str, dict] = {}
    delay = float(os.environ.get("BRAPI_DELAY", "0.2"))

    for ticker in tickers:
        use_modules = ticker in BRAPI_FREE_TICKERS
        try:
            item = _fetch_one(ticker, token, modules=use_modules)
            if item:
                symbol = (item.get("symbol") or ticker).upper()
                item["_has_fundamentals"] = use_modules and bool(
                    item.get("incomeStatementHistory") or item.get("defaultKeyStatistics")
                )
                quotes[symbol] = item
        except Exception:
            pass
        if delay:
            time.sleep(delay)
    return quotes

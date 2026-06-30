import os
import requests

BRAPI_BASE = "https://brapi.dev/api"
BRAPI_FREE_TICKERS = {"PETR4", "VALE3", "ITUB4", "MGLU3"}
BRAPI_MODULES = "incomeStatementHistory,defaultKeyStatistics"
BRAPI_BATCH_SIZE = 10


def get_token() -> str | None:
    return os.environ.get("BRAPI_TOKEN") or None


def fetch_quotes(tickers: list[str], token: str | None = None) -> dict[str, dict]:
    token = token if token is not None else get_token()
    if not token:
        tickers = [t for t in tickers if t in BRAPI_FREE_TICKERS]
    if not tickers:
        return {}

    quotes: dict[str, dict] = {}
    for i in range(0, len(tickers), BRAPI_BATCH_SIZE):
        batch = tickers[i : i + BRAPI_BATCH_SIZE]
        url = f"{BRAPI_BASE}/quote/{','.join(batch)}"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = requests.get(
            url,
            params={"modules": BRAPI_MODULES},
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        for item in r.json().get("results", []):
            symbol = (item.get("symbol") or item.get("requestedSymbol", "")).upper()
            if symbol:
                quotes[symbol] = item
    return quotes

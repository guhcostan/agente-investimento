from unittest.mock import MagicMock, patch

from scripts.brapi_client import BRAPI_FREE_TICKERS, fetch_quotes
from scripts.screener import resolve_provider, score_ticker_brapi


def test_fetch_quotes_without_token_filters_to_free_tickers(monkeypatch):
    monkeypatch.delenv("BRAPI_TOKEN", raising=False)
    monkeypatch.setenv("BRAPI_DELAY", "0")

    def fake_get(url, params=None, headers=None, timeout=30):
        ticker = url.rsplit("/", 1)[-1]
        return MagicMock(
            status_code=200,
            json=lambda: {"results": [{"symbol": ticker, "regularMarketPrice": 35.0}]},
            raise_for_status=lambda: None,
        )

    with patch("scripts.brapi_client.requests.get", side_effect=fake_get) as mock_get:
        quotes = fetch_quotes(["WEGE3", "PETR4", "VALE3"], token=None)

    assert set(quotes.keys()) == {"PETR4", "VALE3"}
    assert mock_get.call_count == 2
    for call in mock_get.call_args_list:
        requested = call.args[0].rsplit("/", 1)[-1]
        assert requested in BRAPI_FREE_TICKERS


def test_fetch_quotes_retries_without_modules_on_403(monkeypatch):
    monkeypatch.setenv("BRAPI_DELAY", "0")
    responses = [
        MagicMock(status_code=403),
        MagicMock(
            status_code=200,
            json=lambda: {"results": [{"symbol": "PETR4", "regularMarketPrice": 38.5}]},
            raise_for_status=lambda: None,
        ),
    ]

    with patch("scripts.brapi_client.requests.get", side_effect=responses) as mock_get:
        quotes = fetch_quotes(["PETR4"], token="test-token")

    assert "PETR4" in quotes
    assert quotes["PETR4"]["_has_fundamentals"] is False
    assert mock_get.call_count == 2
    assert "modules" in mock_get.call_args_list[0].kwargs["params"]
    assert "params" not in mock_get.call_args_list[1].kwargs


def test_score_ticker_brapi_full_score():
    quote = {
        "symbol": "WEGE3",
        "regularMarketPrice": 50.0,
        "regularMarketVolume": 2_000_000,
        "incomeStatementHistory": [
            {"netIncome": 1e9},
            {"netIncome": 1.1e9},
            {"netIncome": 1.2e9},
        ],
        "defaultKeyStatistics": {
            "totalDebt": 100_000_000,
            "ebitda": 1_000_000_000,
            "trailingPE": 6.0,
        },
        "marketCap": 20_000_000_000,
        "_has_fundamentals": True,
    }
    result = score_ticker_brapi(quote, cdi_rate=14.75, novo_mercado={"WEGE3"})
    assert result is not None
    assert result["ticker"] == "WEGE3"
    assert result["score"] == 4


def test_score_ticker_brapi_allows_missing_fundamentals_when_flagged():
    quote = {
        "symbol": "WEGE3",
        "regularMarketPrice": 50.0,
        "regularMarketVolume": 2_000_000,
        "priceEarnings": 5.0,
        "_has_fundamentals": False,
    }
    result = score_ticker_brapi(quote, cdi_rate=14.75, novo_mercado={"WEGE3"})
    assert result is not None
    assert result["score"] == 3


def test_resolve_provider_auto_falls_back_to_brapi(monkeypatch):
    monkeypatch.delenv("DATA_PROVIDER", raising=False)
    with patch("scripts.screener.yfinance_available", return_value=False):
        assert resolve_provider() == "brapi"

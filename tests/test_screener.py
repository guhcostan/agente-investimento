from unittest.mock import patch, MagicMock
import pandas as pd
from scripts.screener import score_ticker, run_screener


def _mock_ticker(avg_volume=2_000_000, price=40.0, net_incomes=None,
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
    # yfinance: financials rows=metrics, cols=dates; loc["Net Income"] → Series of values
    mock.financials = pd.DataFrame(
        [net_incomes],
        index=["Net Income"],
        columns=[f"2{2025 - i}" for i in range(len(net_incomes))],
    )
    return mock


def test_eliminated_by_low_liquidity():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(avg_volume=100)):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is None


def test_eliminated_by_recurring_losses():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        net_incomes=[-1e9, 1e9, -1e9, 1e9]
    )):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is None


def test_full_score_novo_mercado():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        avg_volume=2_000_000, price=50.0, pe=6.0,
        total_debt=100_000_000, ebitda=1_000_000_000,
    )):
        result = score_ticker("WEGE3", cdi_rate=14.75, novo_mercado={"WEGE3"})
    assert result is not None
    assert result["score"] == 4
    assert result["ticker"] == "WEGE3"


def test_zero_score_no_governance_high_pe():
    with patch("scripts.screener.yf.Ticker", return_value=_mock_ticker(
        avg_volume=2_000_000, price=50.0, pe=50.0,
        total_debt=5_000_000_000, ebitda=1_000_000_000,
    )):
        result = score_ticker("FAKE3", cdi_rate=14.75, novo_mercado=set())
    assert result is not None
    assert result["score"] == 0


def test_run_screener_returns_sorted():
    side_effects = [
        {"ticker": "A", "score": 2, "price": 10.0, "reasons": [], "pe": 10, "market_cap": 1e9},
        {"ticker": "B", "score": 4, "price": 20.0, "reasons": [], "pe": 8, "market_cap": 2e9},
        {"ticker": "C", "score": 1, "price": 5.0, "reasons": [], "pe": 15, "market_cap": 5e8},
    ]
    with patch("scripts.screener.score_ticker", side_effect=side_effects), \
         patch("scripts.screener.fetch_novo_mercado", return_value=set()):
        top = run_screener(cdi_rate=14.75, tickers=["A", "B", "C"])
    assert top[0]["ticker"] == "B"
    assert top[0]["score"] == 4

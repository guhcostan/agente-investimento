from unittest.mock import patch, MagicMock
from scripts.macro import get_macro, format_macro


def test_get_macro_returns_expected_keys():
    with patch("scripts.macro.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: [{"valor": "14.75"}],
            raise_for_status=lambda: None,
        )
        result = get_macro()
    assert set(result.keys()) == {"selic", "cdi", "ipca_12m", "usd_brl"}
    assert result["selic"] == 14.75
    assert result["usd_brl"] == 14.75


def test_get_macro_parses_comma_decimal():
    with patch("scripts.macro.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            json=lambda: [{"valor": "10,50"}],
            raise_for_status=lambda: None,
        )
        result = get_macro()
    assert result["cdi"] == 10.50


def test_format_macro_contains_keys():
    macro = {"selic": 14.75, "cdi": 14.65, "ipca_12m": 5.53, "usd_brl": 5.72}
    out = format_macro(macro)
    assert "SELIC" in out
    assert "CDI" in out
    assert "IPCA" in out
    assert "USD" in out

import requests

BCB_SERIES = {
    "selic": 432,
    "cdi": 4389,
    "ipca_12m": 13522,
    "usd_brl": 1,  # PTAX compra — evita yfinance (bloqueado em cloud)
}


def get_macro() -> dict:
    result = {}
    for name, series_id in BCB_SERIES.items():
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados/ultimos/1?formato=json"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        valor = r.json()[0]["valor"].replace(",", ".")
        result[name] = float(valor)

    return result


def format_macro(macro: dict) -> str:
    return (
        f"SELIC: {macro['selic']:.2f}% | "
        f"CDI: {macro['cdi']:.2f}% | "
        f"IPCA 12m: {macro['ipca_12m']:.2f}% | "
        f"USD/BRL: R${macro['usd_brl']:.2f}"
    )

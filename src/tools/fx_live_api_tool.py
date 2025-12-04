import requests

API_BASE = "https://open.er-api.com/v6/latest/"


def get_live_fx_rate(from_currency: str, to_currency: str):
    """
    Fetch live FX rate using open.er-api.com (no API key required).
    Example: https://open.er-api.com/v6/latest/JPY
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    try:
        # Fetch all conversion rates from FROM currency
        url = f"{API_BASE}{from_currency}"
        resp = requests.get(url, timeout=5)
        data = resp.json()

        if data.get("result") != "success":
            return None

        rates = data.get("rates", {})
        rate = rates.get(to_currency)

        if rate:
            return float(rate)

        return None

    except Exception:
        return None

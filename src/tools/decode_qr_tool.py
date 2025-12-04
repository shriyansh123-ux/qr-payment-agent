from typing import Dict

def decode_qr(payload: str) -> Dict:
    """
    Very simple parser for demo payloads of the form: "QR:<COUNTRY>:<CUR>:<AMOUNT>"

    Example: "QR:JP:JPY:1500"
    """
    try:
        _, country, currency, amount_str = payload.split(":")
        amount = float(amount_str)
    except Exception:
        # Fallback mock
        country, currency, amount = "JP", "JPY", 1500.0

    return {
        "merchant_id": "M12345",
        "country": country,
        "currency": currency,
        "amount": amount,
        "raw_fields": {"raw": payload},
    }

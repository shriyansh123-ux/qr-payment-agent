"""Strict parser for demonstrator QR strings and amount-bearing UPI payment URIs.

Neither format verifies the merchant. EMV merchant templates and other national
payment QR formats require separate, scheme-specific implementations.
"""
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Dict
from urllib.parse import urlsplit, parse_qs


_DEMO = re.compile(r"QR:([A-Z]{2}):([A-Z]{3}):([0-9]+(?:\.[0-9]{1,2})?)", re.IGNORECASE)
_CURRENCY = re.compile(r"[A-Z]{3}")
_COUNTRY = re.compile(r"[A-Z]{2}")
_PAYEE = re.compile(r"[A-Za-z0-9._-]{1,128}@[A-Za-z0-9._-]{1,128}")


def _validate_amount(text):
    if not re.fullmatch(r"(?:0|[1-9]\d*)(?:\.\d{1,2})?", text or ""):
        raise ValueError("QR amount must be a positive decimal with at most 2 places")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid QR amount") from exc
    if not value.is_finite() or not Decimal("0") < value <= Decimal("1000000000"):
        raise ValueError("QR amount must be between zero and one billion")
    return float(value)


class QRParserAgent:
    def handle(self, payload: str) -> Dict[str, Any]:
        payload = (payload or "").strip()
        if not payload or len(payload) > 8192:
            raise ValueError("QR payload must contain 1 to 8192 characters")
        # Commas are separators for demo QR strings only, not inside URL fields.
        parts = re.split(r"[,\n]+", payload) if payload.upper().startswith("QR:") else payload.splitlines()
        parts = [p.strip() for p in parts if p.strip()]
        if not parts or len(parts) > 10:
            raise ValueError("Supply between 1 and 10 QR payloads")
        items = [self._parse_single(p) for p in parts]
        return items[0] if len(items) == 1 else {
            "multiple": True, "count": len(items), "items": items
        }

    def _parse_single(self, payload):
        match = _DEMO.fullmatch(payload)
        if match:
            country, currency, amount = match.groups()
            country, currency = country.upper(), currency.upper()
            if currency == "JPY" and "." in amount:
                raise ValueError("JPY example amounts must be whole units")
            return self._result(None, country, currency, amount, "demo")
        uri = urlsplit(payload)
        if uri.scheme.lower() == "upi" and uri.netloc.lower() == "pay":
            if uri.fragment or not uri.query or uri.path or uri.username:
                raise ValueError("Invalid UPI payment URI")
            pairs = parse_qs(uri.query, keep_blank_values=True, strict_parsing=True)
            for key in ("pa", "am", "cu"):
                if key in pairs and len(pairs[key]) != 1:
                    raise ValueError(f"Duplicate UPI field: {key}")
            payee = pairs.get("pa", [""])[0].strip()
            if not _PAYEE.fullmatch(payee):
                raise ValueError("Missing or invalid UPI payee address")
            if "am" not in pairs:
                raise ValueError("Amount-free UPI QRs are not supported; enter an amount-bearing QR")
            currency = pairs.get("cu", ["INR"])[0].upper()
            if currency != "INR":
                raise ValueError("UPI URI currency must be INR")
            return self._result(payee, "IN", currency, pairs["am"][0], "upi")
        raise ValueError("Unsupported QR format: use QR:JP:JPY:1500 or an amount-bearing UPI URI")

    @staticmethod
    def _result(merchant_id, country, currency, amount_raw, scheme):
        if not _COUNTRY.fullmatch(country) or not _CURRENCY.fullmatch(currency):
            raise ValueError("Invalid country or currency code")
        return {
            "merchant_id": merchant_id,
            "merchant_verified": False,
            "country": country,
            "currency": currency,
            "amount": _validate_amount(amount_raw),
            "raw_fields": {"scheme": scheme},
            "qr_id": uuid.uuid4().hex,
        }

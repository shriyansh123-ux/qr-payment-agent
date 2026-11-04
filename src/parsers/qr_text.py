"""Strict parser for demo QR strings, amount-bearing UPI URIs and a subset of EMV QR.

None of these formats verifies the merchant. Other national payment QR formats
need their own scheme-specific parsers.
"""
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, urlsplit

from src.money import minor_units
from src.parsers.emv import parse_emv_qr

MAX_PAYLOAD_CHARS = 8192
MAX_ITEMS = 10

_DEMO = re.compile(r"QR:([A-Z]{2}):([A-Z]{3}):([0-9]+(?:\.[0-9]{1,2})?)", re.IGNORECASE)
_CURRENCY = re.compile(r"[A-Z]{3}")
_COUNTRY = re.compile(r"[A-Z]{2}")
_PAYEE = re.compile(r"[A-Za-z0-9._-]{1,128}@[A-Za-z0-9._-]{1,128}")
_AMOUNT = re.compile(r"(?:0|[1-9]\d*)(?:\.\d{1,2})?")


def _validate_amount(text: str, currency: str) -> Decimal:
    if not _AMOUNT.fullmatch(text or ""):
        raise ValueError("QR amount must be a positive decimal with at most 2 places")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("Invalid QR amount") from exc
    if not value.is_finite() or not Decimal("0") < value <= Decimal("1000000000"):
        raise ValueError("QR amount must be between zero and one billion")
    if minor_units(currency) == 0 and value != value.to_integral_value():
        raise ValueError(f"{currency} amounts must be whole units")
    return value


def split_payloads(payload: str) -> list[str]:
    """Split multi-QR input. Commas only separate demo strings, never URL fields."""
    payload = (payload or "").strip()
    if not payload or len(payload) > MAX_PAYLOAD_CHARS:
        raise ValueError(f"QR payload must contain 1 to {MAX_PAYLOAD_CHARS} characters")
    parts = re.split(r"[,\n]+", payload) if payload.upper().startswith("QR:") else payload.splitlines()
    parts = [p.strip() for p in parts if p.strip()]
    if not parts or len(parts) > MAX_ITEMS:
        raise ValueError(f"Supply between 1 and {MAX_ITEMS} QR payloads")
    return parts


def is_demo_payload(payload: str) -> bool:
    """True when every QR in ``payload`` uses the synthetic ``QR:CC:CUR:amount`` format."""
    try:
        return all(_DEMO.fullmatch(part) for part in split_payloads(payload))
    except ValueError:
        return False


class QRParser:
    def parse(self, payload: str) -> list[dict[str, Any]]:
        """Parse one or more QR payloads into a list of validated items."""
        return [self._parse_single(part) for part in split_payloads(payload)]

    def _parse_single(self, payload: str) -> dict[str, Any]:
        match = _DEMO.fullmatch(payload)
        if match:
            country, currency, amount = match.groups()
            return self._result(None, country.upper(), currency.upper(), amount, "demo")
        if payload.startswith("000201"):
            parsed = parse_emv_qr(payload)
            result = self._result(None, parsed["country"], parsed["currency"],
                                  parsed["amount_raw"], "emv-mpm")
            result["raw_fields"]["merchant_name_claim"] = parsed["merchant_name_claim"]
            return result
        uri = urlsplit(payload)
        if uri.scheme.lower() == "upi" and uri.netloc.lower() == "pay":
            return self._parse_upi(uri)
        raise ValueError("Unsupported QR format: use a demo QR, amount-bearing UPI URI, "
                         "or supported EMV merchant QR")

    def _parse_upi(self, uri) -> dict[str, Any]:
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

    @staticmethod
    def _result(merchant_id, country, currency, amount_raw, scheme) -> dict[str, Any]:
        if not _COUNTRY.fullmatch(country) or not _CURRENCY.fullmatch(currency):
            raise ValueError("Invalid country or currency code")
        return {
            "merchant_id": merchant_id,
            "merchant_verified": False,
            "country": country,
            "currency": currency,
            "amount": _validate_amount(amount_raw, currency),
            "raw_fields": {"scheme": scheme},
            "qr_id": uuid.uuid4().hex,
        }

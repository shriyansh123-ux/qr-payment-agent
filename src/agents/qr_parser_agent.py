import re
import uuid
from typing import Dict, Any, List


class QRParserAgent:
    """
    Parses one or multiple QR payloads.

    Supported formats:
    - QR:JP:JPY:1500
    - QR:JP:JPY:1500,QR:US:USD:12
    - newline separated
    - accidental python list string: "['QR:JP:JPY:1500']"
    """

    def handle(self, payload: str) -> Dict[str, Any]:
        payload = (payload or "").strip()

        # Optional hardening: if payload looks like a python list repr
        # e.g. "['QR:JP:JPY:1500']" or '["QR:JP:JPY:1500","QR:US:USD:12"]'
        if payload.startswith("[") and payload.endswith("]"):
            payload = payload[1:-1].strip()
            payload = payload.replace('"', "").replace("'", "")

        # Split into parts by commas/newlines
        parts = re.split(r"[,\n]+", payload)
        parts = [p.strip() for p in parts if p.strip()]

        items: List[Dict[str, Any]] = []
        for p in parts:
            items.append(self._parse_single(p))

        # Single
        if len(items) == 1:
            return items[0]

        # Multiple
        return {"multiple": True, "count": len(items), "items": items}

    def _parse_single(self, payload: str) -> Dict[str, Any]:
        """
        Parse single QR: QR:JP:JPY:1500
        """
        payload = payload.strip()

        parts = payload.split(":")
        if len(parts) != 4 or parts[0].strip().upper() != "QR":
            raise ValueError(f"Invalid QR payload format: {payload}")

        _, country, currency, amount_raw = parts
        country = country.strip().upper()
        currency = currency.strip().upper()

        # Hardening: sometimes amount comes like "1500']" or "1500 "
        # extract first float-looking number
        amount_raw = amount_raw.strip()
        m = re.search(r"[-+]?\d+(\.\d+)?", amount_raw)
        if not m:
            raise ValueError(f"Invalid amount in QR payload: {payload}")
        amount = float(m.group(0))

        return {
            "merchant_id": "M12345",
            "country": country,
            "currency": currency,
            "amount": amount,
            "raw_fields": {"raw": payload},
            "qr_id": uuid.uuid4().hex,
        }

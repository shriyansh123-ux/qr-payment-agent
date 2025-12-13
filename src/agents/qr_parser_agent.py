import re
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union


class QRParserAgent:
    """
    Parses one or multiple QR payloads.

    Supported formats:
    - QR:JP:JPY:1500
    - QR:JP:JPY:1500,QR:US:USD:12
    - newline separated
    - payload can also arrive as:
        * ["QR:JP:JPY:1500"] (list)
        * "['QR:JP:JPY:1500']" (python list-as-string)
    """

    # Strict pattern: QR:<CC>:<CCC>:<amount>
    # - CC: 2 letters
    # - CCC: 3 letters
    # - amount: int or float
    QR_PATTERN = re.compile(
        r"^\s*QR:([A-Za-z]{2}):([A-Za-z]{3}):([0-9]+(?:\.[0-9]+)?)\s*$"
    )

    def handle(self, payload: Union[str, List[Any], Tuple[Any, ...], None], strict: bool = False) -> Dict[str, Any]:
        """
        strict=False (recommended):
          - skips invalid parts instead of crashing (good for noisy image decode)
        strict=True:
          - raises ValueError on the first invalid part
        """
        normalized = self._normalize_payload(payload)

        # Split into possible multiple QR payloads (comma or newline)
        parts = re.split(r"[,\n]+", normalized)
        parts = [p.strip() for p in parts if p and p.strip()]

        items: List[Dict[str, Any]] = []
        invalid_parts: List[str] = []

        for p in parts:
            try:
                items.append(self._parse_single(p))
            except ValueError:
                if strict:
                    raise
                invalid_parts.append(p)

        if not items:
            # Nothing parseable found
            msg = "No valid QR items found in the provided input."
            if invalid_parts:
                msg += f" Invalid segments: {invalid_parts[:3]}"  # keep short
            raise ValueError(msg)

        # Single QR
        if len(items) == 1:
            return items[0]

        # Multiple QRs
        return {
            "multiple": True,
            "count": len(items),
            "items": items,
            # optional debug info (handy when strict=False)
            "invalid_count": len(invalid_parts),
        }

    def _normalize_payload(self, payload: Union[str, List[Any], Tuple[Any, ...], None]) -> str:
        """
        Normalize payload into a clean string.
        Handles:
          - None
          - list/tuple of strings
          - python-list-string format "['QR:..']"
        """
        if payload is None:
            return ""

        # list/tuple -> join with comma
        if isinstance(payload, (list, tuple)):
            parts = [str(x).strip() for x in payload if str(x).strip()]
            return ",".join(parts)

        s = str(payload).strip()

        # Handle python list-as-string: "['QR:JP:JPY:1500']"
        # We'll try to extract QR tokens from it safely.
        if s.startswith("[") and s.endswith("]"):
            # extract all QR:*:*:* patterns inside
            found = re.findall(r"QR:[A-Za-z]{2}:[A-Za-z]{3}:[0-9]+(?:\.[0-9]+)?", s)
            if found:
                return ",".join(found)
            # fallback: remove brackets + quotes
            s = s.strip("[]").strip().strip("'\"").strip()

        return s

    def _parse_single(self, payload: str) -> Dict[str, Any]:
        """
        Parse single QR: QR:JP:JPY:1500
        Uses regex to avoid float conversion issues like "1500']"
        """
        m = self.QR_PATTERN.match(payload)
        if not m:
            raise ValueError(f"Invalid QR payload format: {payload}")

        country, currency, amount_str = m.group(1), m.group(2), m.group(3)

        return {
            "merchant_id": "M12345",
            "country": country.upper(),
            "currency": currency.upper(),
            "amount": float(amount_str),
            "raw_fields": {"raw": payload.strip()},
            "qr_id": uuid.uuid4().hex,
        }

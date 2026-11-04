"""Supported currency catalog, fetched from Frankfurter and cached for an hour."""
import re
import threading
import time
from datetime import date

import requests

from src.services.fx import FRANKFURTER, TIMEOUT_SECONDS, FXUnavailable

CATALOG_TTL_SECONDS = 3600
_REFERENCE_UNITS = {"XAU", "XAG", "XPD", "XPT", "XDR", "CMD"}
_catalog: tuple[dict, ...] | None = None
_catalog_until = 0.0
_catalog_lock = threading.Lock()


def _fetch_catalog() -> tuple[dict, ...]:
    response = requests.get(f"{FRANKFURTER}/v2/currencies", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or not 1 <= len(rows) <= 500:
        raise ValueError("Invalid currency catalog")
    currencies = {}
    for row in rows:
        code, name = row.get("iso_code"), row.get("name")
        if (not isinstance(code, str) or not re.fullmatch(r"[A-Z]{3}", code)
                or not isinstance(name, str) or not 1 <= len(name) <= 120):
            raise ValueError("Invalid currency entry")
        # Exclude historical-only entries and non-currency reference units.
        observed = date.fromisoformat(row["end_date"])
        if code not in _REFERENCE_UNITS and 0 <= (date.today() - observed).days <= 7:
            currencies[code] = {"code": code, "name": name}
    if not currencies:
        raise ValueError("No recent currencies")
    return tuple(currencies[code] for code in sorted(currencies))


def supported_currencies() -> list[dict]:
    global _catalog, _catalog_until
    with _catalog_lock:
        if _catalog is not None and _catalog_until > time.monotonic():
            return list(_catalog)
    # Fetch outside the lock so a slow provider does not queue every request.
    try:
        catalog = _fetch_catalog()
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise FXUnavailable("Supported currency list is temporarily unavailable. Try again.") from exc
    with _catalog_lock:
        _catalog, _catalog_until = catalog, time.monotonic() + CATALOG_TTL_SECONDS
    return list(catalog)


def supported_codes() -> set[str]:
    return {entry["code"] for entry in supported_currencies()}

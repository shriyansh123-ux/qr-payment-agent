"""Manual reference conversion; independent of QR parsing and payment routing."""
from datetime import date
from decimal import Decimal
import re
import threading
import time

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.agents.fx_rate_agent import FXRateAgent, FXUnavailable

_catalog = None
_catalog_until = 0
_catalog_lock = threading.Lock()
_REFERENCE_UNITS = {"XAU", "XAG", "XPD", "XPT", "XDR", "CMD"}


def supported_currencies():
    global _catalog, _catalog_until
    with _catalog_lock:
        if _catalog is not None and _catalog_until > time.monotonic():
            return list(_catalog)
        try:
            response = requests.get("https://api.frankfurter.dev/v2/currencies", timeout=8)
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
            _catalog = tuple(currencies[code] for code in sorted(currencies))
            _catalog_until = time.monotonic() + 3600
            return list(_catalog)
        except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError) as exc:
            raise FXUnavailable("Supported currency list is temporarily unavailable. Try again.") from exc


class ConversionRequest(BaseModel):
    amount: Decimal = Field(gt=0, le=1000000000000, max_digits=19, decimal_places=6)
    from_currency: str = Field(pattern=r"^[A-Z]{3}$")
    to_currency: str = Field(pattern=r"^[A-Z]{3}$")


def converter_router(auth):
    router = APIRouter(tags=["currency-converter"])

    @router.get("/api/currencies")
    def currencies():
        try:
            return {"currencies": supported_currencies(), "source": "frankfurter-reference"}
        except FXUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc

    @router.post("/api/convert", dependencies=[Depends(auth)])
    def convert(body: ConversionRequest):
        try:
            codes = {entry["code"] for entry in supported_currencies()}
            if body.from_currency not in codes or body.to_currency not in codes:
                raise HTTPException(422, "Choose currencies from the supported list.")
            result = FXRateAgent().handle(body.amount, body.from_currency, body.to_currency)
        except FXUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"amount": str(body.amount), **result}

    return router

"""Reference FX conversion. Never invents a rate when the provider fails."""
import logging
import time
from datetime import date
from decimal import Decimal, InvalidOperation

import requests

from src.money import quantize

logger = logging.getLogger(__name__)

FRANKFURTER = "https://api.frankfurter.dev"
TIMEOUT_SECONDS = 8
MAX_RATE_AGE_DAYS = 7
# (base, quote) -> (rate, observation date, provider, monotonic expiry)
_RATE_CACHE: dict[tuple[str, str], tuple[Decimal, str, str, float]] = {}


class FXUnavailable(RuntimeError):
    """The reference exchange rate could not be retrieved safely."""


def _amount(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid transaction amount") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Transaction amount must be positive and finite")
    return amount


def _checked(rate_value, date_text) -> tuple[Decimal, str]:
    rate = Decimal(str(rate_value))
    observed = date.fromisoformat(date_text)
    age = (date.today() - observed).days
    if not rate.is_finite() or rate <= 0 or not 0 <= age <= MAX_RATE_AGE_DAYS:
        raise ValueError("Missing, invalid, or stale reference rate")
    return rate, observed.isoformat()


class FXRateService:
    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl_seconds = cache_ttl_seconds

    def _fetch_live_rate(self, from_cur: str, to_cur: str) -> tuple[Decimal, str]:
        """Frankfurter blended v2 reference rate (not an executable bank quote)."""
        try:
            response = requests.get(f"{FRANKFURTER}/v2/rate/{from_cur}/{to_cur}", timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return _checked(data["rate"], data["date"])
        except (requests.RequestException, KeyError, ValueError, TypeError, InvalidOperation) as exc:
            logger.warning("Reference FX unavailable for %s/%s: %s", from_cur, to_cur, type(exc).__name__)
            raise FXUnavailable(f"Reference FX rate unavailable for {from_cur}/{to_cur}") from exc

    def _fetch_ecb_rate(self, from_cur: str, to_cur: str) -> tuple[Decimal, str]:
        """Independent ECB series through Frankfurter's v1 endpoint, used as a fallback."""
        try:
            response = requests.get(f"{FRANKFURTER}/v1/latest",
                                    params={"base": from_cur, "symbols": to_cur},
                                    timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return _checked(data["rates"][to_cur], data["date"])
        except (requests.RequestException, KeyError, ValueError, TypeError, InvalidOperation) as exc:
            logger.warning("ECB reference FX unavailable for %s/%s: %s", from_cur, to_cur, type(exc).__name__)
            raise FXUnavailable(f"Reference FX rate unavailable for {from_cur}/{to_cur}") from exc

    def get_rate(self, from_cur: str, to_cur: str) -> tuple[Decimal, str, str]:
        from_cur = (from_cur or "").strip().upper()
        to_cur = (to_cur or "").strip().upper()
        if not (len(from_cur) == len(to_cur) == 3 and from_cur.isalpha() and to_cur.isalpha()):
            raise ValueError("Invalid ISO currency code")
        if from_cur == to_cur:
            return Decimal("1"), date.today().isoformat(), "same-currency"
        key = (from_cur, to_cur)
        cached = _RATE_CACHE.get(key)
        if cached and cached[3] > time.monotonic():
            return cached[0], cached[1], cached[2] + " (cached)"
        try:
            rate, observed = self._fetch_live_rate(from_cur, to_cur)
            provider = "frankfurter-reference"
        except FXUnavailable:
            rate, observed = self._fetch_ecb_rate(from_cur, to_cur)
            provider = "frankfurter-ecb-reference"
        _RATE_CACHE[key] = (rate, observed, provider, time.monotonic() + self.cache_ttl_seconds)
        return rate, observed, provider

    def convert(self, amount_local, local_currency: str, home_currency: str) -> dict:
        amount = _amount(amount_local)
        base = (local_currency or "").strip().upper()
        quote = (home_currency or "").strip().upper()
        rate, observed, provider = self.get_rate(base, quote)
        # Provider fees cannot be known from a QR code, so none are invented.
        converted = quantize(amount * rate, quote)
        return {
            "from_currency": base,
            "to_currency": quote,
            "rate": rate,
            "rate_date": observed,
            "base_home": converted,
            "markup_home": Decimal(0),
            "network_fee_home": Decimal(0),
            "total_home": converted,
            "fee_status": "not_quoted",
            "notes": "Reference FX estimate before provider spread and fees; not a final payable quote.",
            "provider": provider,
        }

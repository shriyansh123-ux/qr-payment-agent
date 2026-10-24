"""Reference FX conversion. Never invent a currency rate on provider failure."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import time

import requests

logger = logging.getLogger(__name__)
_RATE_CACHE = {}  # (base, quote): (Decimal rate, observation date, provider, expiration)


class FXUnavailable(RuntimeError):
    """The reference exchange rate could not be retrieved safely."""


def _amount(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid transaction amount") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Transaction amount must be positive and finite")
    return amount


class FXRateAgent:
    def __init__(self, cache_ttl_seconds=300):
        self.cache_ttl_seconds = cache_ttl_seconds

    def _fetch_live_rate(self, from_cur, to_cur):
        """Frankfurter reference rate, not an executable card/bank quote."""
        try:
            r = requests.get(
                f"https://api.frankfurter.dev/v2/rate/{from_cur}/{to_cur}",
                timeout=8,
            )
            r.raise_for_status()
            data = r.json()
            rate = Decimal(str(data["rate"]))
            observed = date.fromisoformat(data["date"])
            if (not rate.is_finite() or rate <= 0 or
                    (date.today() - observed).days > 7 or observed > date.today()):
                raise ValueError("Missing, invalid, or stale reference rate")
            return rate, observed.isoformat()
        except (requests.RequestException, KeyError, ValueError, TypeError, InvalidOperation) as exc:
            logger.warning("Reference FX unavailable for %s/%s: %s", from_cur, to_cur, type(exc).__name__)
            raise FXUnavailable(f"Reference FX rate unavailable for {from_cur}/{to_cur}") from exc

    def _fetch_ecb_rate(self, from_cur, to_cur):
        """Independent ECB reference series through Frankfurter's maintained v1 endpoint.

        The deprecated v1 API is still supported. Do not combine two potentially
        stale rates or silently substitute a fictional rate.
        """
        try:
            response = requests.get(
                "https://api.frankfurter.dev/v1/latest",
                params={"base": from_cur, "symbols": to_cur},
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            rate = Decimal(str(data["rates"][to_cur]))
            observed = date.fromisoformat(data["date"])
            if (not rate.is_finite() or rate <= 0 or
                    not 0 <= (date.today() - observed).days <= 7):
                raise ValueError("Missing, invalid, or stale ECB reference rate")
            return rate, observed.isoformat()
        except (requests.RequestException, KeyError, ValueError, TypeError, InvalidOperation) as exc:
            logger.warning("ECB reference FX unavailable for %s/%s: %s",
                           from_cur, to_cur, type(exc).__name__)
            raise FXUnavailable(f"Reference FX rate unavailable for {from_cur}/{to_cur}") from exc

    def get_rate(self, from_cur, to_cur):
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
            # Fall back to a distinct, dated ECB series, not an invented rate.
            rate, observed = self._fetch_ecb_rate(from_cur, to_cur)
            provider = "frankfurter-ecb-reference"
        _RATE_CACHE[key] = (rate, observed, provider, time.monotonic() + self.cache_ttl_seconds)
        return rate, observed, provider

    def usd_equivalent(self, amount_local, local_currency):
        rate, _, _ = self.get_rate(local_currency, "USD")
        return _amount(amount_local) * rate

    def handle(self, amount_local, local_currency, home_currency):
        amount = _amount(amount_local)
        base = (local_currency or "").strip().upper()
        quote = (home_currency or "").strip().upper()
        rate, observed, provider = self.get_rate(base, quote)
        # Provider-specific fees cannot be known from a QR code: do not fabricate any.
        converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "from_currency": base,
            "to_currency": quote,
            "rate": float(rate),
            "rate_date": observed,
            "base_home": float(converted),
            "markup_home": 0.0,
            "network_fee_home": 0.0,
            "total_home": float(converted),
            "fee_status": "not_quoted",
            "notes": "Reference FX estimate before provider spread and fees; not a final payable quote.",
            "provider": provider,
        }

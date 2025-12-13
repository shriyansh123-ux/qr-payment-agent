import time
import logging
import requests

logger = logging.getLogger(__name__)

# Small in-memory cache to reduce API calls
_RATE_CACHE = {}  # (from,to) -> (rate, expires_at)


class FXRateAgent:
    def __init__(self):
        self.cache_ttl_seconds = 300  # 5 min cache

    def _get_cached_rate(self, from_cur: str, to_cur: str):
        key = (from_cur, to_cur)
        if key in _RATE_CACHE:
            rate, exp = _RATE_CACHE[key]
            if time.time() < exp:
                return rate
        return None

    def _set_cached_rate(self, from_cur: str, to_cur: str, rate: float):
        key = (from_cur, to_cur)
        _RATE_CACHE[key] = (rate, time.time() + self.cache_ttl_seconds)

    def _fetch_live_rate(self, from_cur: str, to_cur: str) -> float:
        # exchangerate.host (no key) – can sometimes fail depending on network / service
        url = "https://api.exchangerate.host/convert"
        params = {"from": from_cur, "to": to_cur, "amount": 1}

        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        # exchangerate.host returns "result" for amount=1
        rate = data.get("result")
        if rate is None:
            raise ValueError(f"Live FX response missing 'result': {data}")

        return float(rate)

    def _mock_rate(self, from_cur: str, to_cur: str) -> float:
        # Your current mock fallback
        if from_cur == "JPY" and to_cur == "INR":
            return 0.55
        if from_cur == "USD" and to_cur == "INR":
            return 83.0
        return 1.0

    def handle(self, amount_local: float, local_currency: str, home_currency: str):
        from_cur = (local_currency or "").upper()
        to_cur = (home_currency or "").upper()

        # 1) Cache
        cached = self._get_cached_rate(from_cur, to_cur)
        if cached is not None:
            rate = cached
            provider = "cache"
        else:
            # 2) Try live with retry
            provider = "exchangerate.host-live"
            rate = None
            last_err = None
            for attempt in range(2):  # 2 attempts
                try:
                    rate = self._fetch_live_rate(from_cur, to_cur)
                    self._set_cached_rate(from_cur, to_cur, rate)
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(0.7)

            # 3) Fallback to mock ONLY if live fails
            if rate is None:
                provider = "mock-fx"
                rate = self._mock_rate(from_cur, to_cur)
                logger.warning("Live FX failed, using mock rate for %s -> %s: %s (%s)", from_cur, to_cur, rate, last_err)

        # Apply a simple markup + fixed network fee like before
        base_home = float(amount_local) * float(rate)
        markup_home = 0.03 * base_home
        network_fee_home = 11.0
        total_home = base_home + markup_home + network_fee_home

        notes = "Live FX rate from exchangerate.host with standard markup." if provider != "mock-fx" else "Mock FX fallback (live failed)."

        return {
            "from_currency": from_cur,
            "to_currency": to_cur,
            "rate": float(rate),
            "base_home": float(base_home),
            "markup_home": float(markup_home),
            "network_fee_home": float(network_fee_home),
            "total_home": float(total_home),
            "notes": notes,
            "provider": provider,
        }

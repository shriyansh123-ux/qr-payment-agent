"""Offline rate limiter tests with controlled monotonic clock."""
import asyncio
from types import SimpleNamespace

from src.api import limits


class Request:
    def __init__(self, path="/api/scan-text", host="local-test-client"):
        self.url = SimpleNamespace(path=path)
        self.client = SimpleNamespace(host=host)


async def next_response(request):
    return SimpleNamespace(status_code=200)


def test_api_rate_limiter_blocks_and_sends_retry_after(monkeypatch):
    limits._buckets.clear()
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(limits.time, "monotonic", lambda: 1000)
    for _ in range(30):
        assert asyncio.run(limits.api_rate_limit(Request(), next_response)).status_code == 200
    failure = asyncio.run(limits.api_rate_limit(Request(), next_response))
    assert failure.status_code == 429
    assert failure.headers["retry-after"] == "60"
    limits._buckets.clear()


def test_health_not_rate_limited():
    result = asyncio.run(limits.api_rate_limit(Request(path="/api/health"), next_response))
    assert result.status_code == 200



def test_login_has_stricter_throttling(monkeypatch):
    limits._buckets.clear()
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setattr(limits.time, "monotonic", lambda: 2000)
    route = Request(path="/api/account/login", host="synthetic-auth-client")
    for _ in range(6):
        assert asyncio.run(limits.api_rate_limit(route, next_response)).status_code == 200
    assert asyncio.run(limits.api_rate_limit(route, next_response)).status_code == 429
    limits._buckets.clear()

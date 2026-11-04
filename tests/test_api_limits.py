"""Offline rate limiter tests with controlled monotonic clock."""
import asyncio
from types import SimpleNamespace

from src.api import limits


class Request:
    def __init__(self, path="/api/scan-text", host="local-test-client"):
        self.url = SimpleNamespace(path=path)
        self.client = SimpleNamespace(host=host)
        self.headers = {}


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


class ProxiedRequest(Request):
    def __init__(self, forwarded, host="10.0.0.1"):
        super().__init__(host=host)
        self.headers = {"x-forwarded-for": forwarded}


def test_forwarded_header_ignored_unless_proxy_trusted(monkeypatch):
    monkeypatch.delenv("QR_TRUSTED_PROXY_HOPS", raising=False)
    assert limits.client_address(ProxiedRequest("203.0.113.9")) == "10.0.0.1"


def test_trusted_proxy_uses_rightmost_unspoofable_entry(monkeypatch):
    monkeypatch.setenv("QR_TRUSTED_PROXY_HOPS", "1")
    # A client can prepend fake entries; the proxy-appended one is last.
    assert limits.client_address(ProxiedRequest("1.2.3.4, 198.51.100.7")) == "198.51.100.7"
    assert limits.client_address(ProxiedRequest("")) == "10.0.0.1"


def test_visitors_behind_one_proxy_get_separate_buckets(monkeypatch):
    limits._buckets.clear()
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("QR_TRUSTED_PROXY_HOPS", "1")
    monkeypatch.setattr(limits.time, "monotonic", lambda: 3000)
    login = "/api/account/login"
    for _ in range(6):
        request = ProxiedRequest("198.51.100.1")
        request.url.path = login
        assert asyncio.run(limits.api_rate_limit(request, next_response)).status_code == 200
    other = ProxiedRequest("198.51.100.2")
    other.url.path = login
    assert asyncio.run(limits.api_rate_limit(other, next_response)).status_code == 200
    limits._buckets.clear()

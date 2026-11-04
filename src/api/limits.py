"""Best-effort throttling: Redis shared counters if configured, else bounded memory.

Client address: behind a reverse proxy (Render, Fly, a load balancer) the TCP peer
is the proxy, so every visitor would share one bucket. Set
``QR_TRUSTED_PROXY_HOPS`` to the number of proxies in front of the app; the
client is then read from ``X-Forwarded-For`` counting from the right, which a
client cannot spoof by sending its own header. The default of 0 ignores the header.

Not a substitute for an identity-aware WAF / anti-abuse controls.
"""
import os
import threading
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi.responses import JSONResponse

WINDOW_SECONDS = 60
_LIMITS = {"/api/account/login": 6, "/api/account/register": 4, "/api/convert": 30,
           "/api/account/scan-text": 30}
_SCAN_LIMIT = 30
_DEFAULT_LIMIT = 60
_MAX_BUCKETS = 4000
_lock = threading.Lock()
_buckets: defaultdict[str, deque] = defaultdict(deque)


def limit_for(path: str) -> int:
    return _LIMITS.get(path, _SCAN_LIMIT if path.startswith("/api/scan") else _DEFAULT_LIMIT)


def client_address(request) -> str:
    peer = request.client.host if request.client else "unknown"
    try:
        hops = int(os.getenv("QR_TRUSTED_PROXY_HOPS", "0"))
    except ValueError:
        hops = 0
    if hops <= 0:
        return peer
    forwarded = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
    # Each trusted proxy appends the address it received the request from.
    return forwarded[-hops] if len(forwarded) >= hops else peer


@lru_cache(maxsize=4)
def _redis_client(url: str):
    import redis
    return redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)


def _redis_check(key: str, limit: int):
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        stamp = int(time.time() // WINDOW_SECONDS)
        name = f"qr:limit:{key}:{stamp}"
        with _redis_client(url).pipeline(transaction=True) as pipe:
            pipe.incr(name)
            pipe.expire(name, WINDOW_SECONDS + 5)
            count, _ = pipe.execute()
        return count <= limit
    except Exception:
        # Degraded mode: the local in-process limiter still applies.
        return None


def _local_check(key: str, limit: int) -> bool:
    now = time.monotonic()
    with _lock:
        if len(_buckets) > _MAX_BUCKETS:
            for bucket in list(_buckets):
                if not _buckets[bucket] or now - _buckets[bucket][-1] > WINDOW_SECONDS:
                    del _buckets[bucket]
        queue = _buckets[key]
        while queue and now - queue[0] >= WINDOW_SECONDS:
            queue.popleft()
        if len(queue) >= limit:
            return False
        queue.append(now)
        return True


async def api_rate_limit(request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or path in ("/api/health", "/api/config"):
        return await call_next(request)
    limit = limit_for(path)
    key = f"{path}:{client_address(request)}"
    shared_allowed = _redis_check(key, limit)
    local_allowed = _local_check(key, limit)
    if shared_allowed is False or not local_allowed:
        return JSONResponse(status_code=429, content={"detail": "Too many requests; retry later."},
                            headers={"Retry-After": str(WINDOW_SECONDS)})
    return await call_next(request)

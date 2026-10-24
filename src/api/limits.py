"""Best-effort demo throttling: Redis shared counters if configured, else bounded memory.

No X-Forwarded-For trust; remote address provided by ASGI server is used.
Not a substitute for an identity-aware WAF / anti-abuse controls.
"""
import os
import threading
import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse

_WINDOWS = {"/api/account/login": 6, "/api/account/register": 4}
_lock = threading.Lock()
_buckets = defaultdict(deque)


def _redis_check(key, limit):
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        import redis
        r = redis.Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        # Aligned 60s window and atomic increment; no personally identifying QR content.
        stamp = int(time.time() // 60)
        name = f"qr:limit:{key}:{stamp}"
        with r.pipeline(transaction=True) as pipe:
            pipe.incr(name)
            pipe.expire(name, 65)
            count, _ = pipe.execute()
        return count <= limit
    except Exception:
        # Degraded resilience: local process-only limiter still applies.
        return None


def _local_check(key, limit):
    now = time.monotonic()
    with _lock:
        if len(_buckets) > 4000:
            for bucket in list(_buckets):
                if not _buckets[bucket] or now - _buckets[bucket][-1] > 60:
                    del _buckets[bucket]
        queue = _buckets[key]
        while queue and now - queue[0] >= 60:
            queue.popleft()
        if len(queue) >= limit:
            return False
        queue.append(now)
        return True


async def api_rate_limit(request, call_next):
    path = request.url.path
    if not path.startswith("/api/") or path == "/api/health":
        return await call_next(request)
    limit = _WINDOWS.get(path, 30 if path.startswith("/api/scan") else 60)
    client = request.client.host if request.client else "unknown"
    key = f"{path}:{client}"
    allowed = _redis_check(key, limit)
    # Local check also bounds abusive clients on a shared Redis outage.
    local_allowed = _local_check(key, limit)
    if allowed is False or not local_allowed:
        return JSONResponse(status_code=429, content={"detail": "Too many requests; retry later."},
                            headers={"Retry-After": "60"})
    return await call_next(request)

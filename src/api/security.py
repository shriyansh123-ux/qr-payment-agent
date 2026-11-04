"""Baseline security headers for API responses and the bundled React app."""

# FastAPI's /docs and /redoc pages load assets from a CDN, so they get no CSP.
_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_CSP = "; ".join([
    "default-src 'self'",
    "img-src 'self' data: blob:",
    "style-src 'self' 'unsafe-inline'",
    "script-src 'self'",
    "connect-src 'self'",
    "font-src 'self' data:",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
}


async def security_headers(request, call_next):
    response = await call_next(request)
    for name, value in _HEADERS.items():
        response.headers.setdefault(name, value)
    if not request.url.path.startswith(_DOCS_PATHS):
        response.headers.setdefault("Content-Security-Policy", _CSP)
    return response

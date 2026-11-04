"""Shared API dependencies: the estimator instance and API-key checks.

X-API-Key is a shared developer key, not end-user identity. When public demo
mode is on (the default), visitors can try synthetic ``QR:`` payloads and the
manual converter without a key; real-looking UPI/EMV payloads and image uploads
still require it.
"""
import hmac
import os

from fastapi import Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from src.services.estimator import CostEstimator
from src.services.fx import FXUnavailable

MIN_KEY_LENGTH = 24
estimator = CostEstimator()


def public_demo_enabled() -> bool:
    return os.getenv("QR_PUBLIC_DEMO", "true").strip().lower() == "true"


def check_api_key(x_api_key: str | None) -> None:
    configured = os.getenv("QR_API_KEY", "")
    if len(configured) < MIN_KEY_LENGTH:
        raise HTTPException(503, detail="Server API key is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured):
        raise HTTPException(401, detail="Invalid API key")


def require_api_key(x_api_key: str | None = Header(None)) -> None:
    check_api_key(x_api_key)


def api_key_or_public_demo(x_api_key: str | None = Header(None)) -> None:
    if x_api_key or not public_demo_enabled():
        check_api_key(x_api_key)


async def run_estimate(fn, *args):
    """Run blocking parsing/FX work off the event loop and map errors to HTTP codes."""
    try:
        return await run_in_threadpool(fn, *args)
    except FXUnavailable as exc:
        raise HTTPException(503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

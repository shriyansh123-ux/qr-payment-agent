import pytest

from src.api import limits
from src.services.fx import _RATE_CACHE


@pytest.fixture(autouse=True)
def isolate_shared_state():
    """Rate-limit buckets and the FX cache are module-level; reset them per test."""
    limits._buckets.clear()
    _RATE_CACHE.clear()
    yield
    limits._buckets.clear()
    _RATE_CACHE.clear()

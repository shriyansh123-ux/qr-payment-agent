"""Network-independent checks for financial correctness and API protection."""
import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.parsers.qr_text import QRParser
from src.services.fx import _RATE_CACHE, FXRateService, FXUnavailable


def parse_one(payload):
    [item] = QRParser().parse(payload)
    return item


@pytest.fixture(autouse=True)
def isolate_fx_cache():
    _RATE_CACHE.clear()
    yield
    _RATE_CACHE.clear()


@pytest.mark.parametrize("bad", ["QR:JP:JPY:-5", "QR:JP:JPY:0", "QR:JP:JPY:1hello", "QR:JP:JPY:1.123", "QR:JP:JPY:4junk"])
def test_bad_amounts_are_rejected(bad):
    with pytest.raises(ValueError):
        parse_one(bad)


def test_demo_qr_has_no_fake_merchant():
    assert parse_one("QR:JP:JPY:1500")["merchant_id"] is None


def test_upi_payee_is_unverified():
    item = parse_one("upi://pay?pa=demo@upi&am=12.00&cu=INR")
    assert item["merchant_id"] == "demo@upi" and item["merchant_verified"] is False


def test_fx_never_uses_fake_fallback(monkeypatch):
    agent = FXRateService()
    def broken(*args, **kwargs):
        raise FXUnavailable("offline")
    monkeypatch.setattr(agent, "_fetch_live_rate", broken)
    monkeypatch.setattr(agent, "_fetch_ecb_rate", broken)
    with pytest.raises(FXUnavailable):
        agent.convert(100, "JPY", "INR")


def test_same_currency_has_no_invented_fee():
    data = FXRateService().convert(100, "INR", "INR")
    assert data["total_home"] == 100
    assert data["fee_status"] == "not_quoted"


def test_api_requires_key_when_public_demo_is_off(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", "a-long-local-development-key-123456")
    monkeypatch.setenv("QR_PUBLIC_DEMO", "false")
    with TestClient(app) as client:
        response = client.post("/api/scan-text", json={"qr_payload": "QR:JP:JPY:1500"})
        assert response.status_code == 401


def test_api_rejects_bad_amount(monkeypatch):
    key = "a-long-local-development-key-123456"
    monkeypatch.setenv("QR_API_KEY", key)
    with TestClient(app) as client:
        response = client.post("/api/scan-text", headers={"X-API-Key": key},
                               json={"qr_payload": "QR:JP:JPY:-5"})
        assert response.status_code == 422



def test_fresh_ecb_reference_used_if_blended_provider_is_stale(monkeypatch):
    from datetime import date
    from decimal import Decimal
    agent = FXRateService()
    def stale(*args):
        raise FXUnavailable("stale blended rate")
    monkeypatch.setattr(agent, "_fetch_live_rate", stale)
    monkeypatch.setattr(
        agent, "_fetch_ecb_rate",
        lambda base, quote: (Decimal("0.60"), date.today().isoformat())
    )
    converted = agent.convert(1500, "JPY", "INR")
    assert converted["total_home"] == 900.0
    assert converted["provider"] == "frankfurter-ecb-reference"
    assert converted["rate_date"] == date.today().isoformat()


def test_no_fallback_rate_if_both_reference_feeds_unavailable(monkeypatch):
    agent = FXRateService()
    def fail(*args):
        raise FXUnavailable("provider unavailable")
    monkeypatch.setattr(agent, "_fetch_live_rate", fail)
    monkeypatch.setattr(agent, "_fetch_ecb_rate", fail)
    with pytest.raises(FXUnavailable):
        agent.convert(1500, "JPY", "INR")


def test_ecb_rate_rejects_stale_and_malformed_data(monkeypatch):
    from datetime import date, timedelta
    class Response:
        def __init__(self, body):
            self.body = body
        def raise_for_status(self):
            pass
        def json(self):
            return self.body
    response = Response({
        "date": (date.today() - timedelta(days=10)).isoformat(),
        "rates": {"INR": 0.60},
    })
    monkeypatch.setattr("src.services.fx.requests.get", lambda *a, **k: response)
    with pytest.raises(FXUnavailable):
        FXRateService()._fetch_ecb_rate("JPY", "INR")

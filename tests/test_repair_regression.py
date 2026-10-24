"""Network-independent checks for financial correctness and API protection."""
import os
import pytest
from fastapi.testclient import TestClient
from src.agents.fx_rate_agent import FXRateAgent, FXUnavailable, _RATE_CACHE
from src.agents.qr_parser_agent import QRParserAgent
from src.agents.risk_scorer import RiskScorer
from src.api.server import app


@pytest.fixture(autouse=True)
def isolate_fx_cache():
    _RATE_CACHE.clear()
    yield
    _RATE_CACHE.clear()


@pytest.mark.parametrize("bad", ["QR:JP:JPY:-5", "QR:JP:JPY:0", "QR:JP:JPY:1hello", "QR:JP:JPY:1.123", "QR:JP:JPY:4junk"])
def test_bad_amounts_are_rejected(bad):
    with pytest.raises(ValueError):
        QRParserAgent().handle(bad)


def test_demo_qr_has_no_fake_merchant():
    assert QRParserAgent().handle("QR:JP:JPY:1500")["merchant_id"] is None


def test_upi_payee_is_unverified():
    item = QRParserAgent().handle("upi://pay?pa=demo@upi&am=12.00&cu=INR")
    assert item["merchant_id"] == "demo@upi" and item["merchant_verified"] is False


def test_fx_never_uses_fake_fallback(monkeypatch):
    agent = FXRateAgent()
    def broken(*args, **kwargs):
        raise FXUnavailable("offline")
    monkeypatch.setattr(agent, "_fetch_live_rate", broken)
    monkeypatch.setattr(agent, "_fetch_ecb_rate", broken)
    with pytest.raises(FXUnavailable):
        agent.handle(100, "JPY", "INR")


def test_same_currency_has_no_invented_fee():
    data = FXRateAgent().handle(100, "INR", "INR")
    assert data["total_home"] == 100
    assert data["fee_status"] == "not_quoted"


def test_risk_not_assessed_without_usd_rate():
    assert RiskScorer().evaluate(None, "JP", 500, None)["risk_level"] == "not_assessed"


def test_api_requires_key(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", "a-long-local-development-key-123456")
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
    from decimal import Decimal
    from datetime import date
    agent = FXRateAgent()
    def stale(*args):
        raise FXUnavailable("stale blended rate")
    monkeypatch.setattr(agent, "_fetch_live_rate", stale)
    monkeypatch.setattr(
        agent, "_fetch_ecb_rate",
        lambda base, quote: (Decimal("0.60"), date.today().isoformat())
    )
    converted = agent.handle(1500, "JPY", "INR")
    assert converted["total_home"] == 900.0
    assert converted["provider"] == "frankfurter-ecb-reference"
    assert converted["rate_date"] == date.today().isoformat()


def test_no_fallback_rate_if_both_reference_feeds_unavailable(monkeypatch):
    agent = FXRateAgent()
    def fail(*args):
        raise FXUnavailable("provider unavailable")
    monkeypatch.setattr(agent, "_fetch_live_rate", fail)
    monkeypatch.setattr(agent, "_fetch_ecb_rate", fail)
    with pytest.raises(FXUnavailable):
        agent.handle(1500, "JPY", "INR")


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
    monkeypatch.setattr("src.agents.fx_rate_agent.requests.get", lambda *a, **k: response)
    with pytest.raises(FXUnavailable):
        FXRateAgent()._fetch_ecb_rate("JPY", "INR")

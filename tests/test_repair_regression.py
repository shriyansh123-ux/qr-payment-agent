"""Network-independent checks for financial correctness and API protection."""
import os
import pytest
from fastapi.testclient import TestClient
from src.agents.fx_rate_agent import FXRateAgent, FXUnavailable
from src.agents.qr_parser_agent import QRParserAgent
from src.agents.risk_scorer import RiskScorer
from src.api.server import app


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

"""API contract tests using same-currency requests (no network required)."""
from fastapi.testclient import TestClient

from src.api.server import app

KEY = "local-testing-secret-key-at-least-24-characters"
UPI = "upi://pay?pa=demo@upi&am=100&cu=INR"


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200 and res.json()["status"] == "ok"


def test_authenticated_scan(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    with TestClient(app) as client:
        assert client.post("/api/scan-text", json={"qr_payload": UPI}).status_code == 401
        result = client.post("/api/scan-text", headers={"X-API-Key": KEY}, json={"qr_payload": UPI})
        assert result.status_code == 200
        data = result.json()
        assert data["success"]
        assert data["qr_info"]["merchant_id"] == "demo@upi"
        assert data["fx_result"]["total_home"] == 100
        assert data["fx_result"]["fee_status"] == "not_quoted"
        assert "risk_result" not in data


def test_public_demo_accepts_synthetic_payloads_without_key(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    monkeypatch.setenv("QR_PUBLIC_DEMO", "true")
    with TestClient(app) as client:
        assert client.get("/api/config").json() == {"public_demo": True}
        demo = client.post("/api/scan-text", json={"qr_payload": "QR:IN:INR:100,QR:IN:INR:5"})
        assert demo.status_code == 200, demo.text
        assert demo.json()["total_home"] == 105
        # Real-looking payloads still need the key, even mixed with demo ones.
        assert client.post("/api/scan-text", json={"qr_payload": UPI}).status_code == 401
        assert client.post("/api/scan-text", json={"qr_payload": "QR:IN:INR:1\n" + UPI}).status_code == 401
        # A wrong key is rejected rather than silently ignored.
        wrong = client.post("/api/scan-text", headers={"X-API-Key": "wrong"}, json={"qr_payload": "QR:IN:INR:1"})
        assert wrong.status_code == 401


def test_public_demo_can_be_disabled(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    monkeypatch.setenv("QR_PUBLIC_DEMO", "false")
    with TestClient(app) as client:
        assert client.get("/api/config").json() == {"public_demo": False}
        assert client.post("/api/scan-text", json={"qr_payload": "QR:IN:INR:100"}).status_code == 401


def test_removed_session_endpoints_are_gone(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    with TestClient(app) as client:
        assert client.get("/api/history", headers={"X-API-Key": KEY}).status_code in (404, 405)


def test_security_headers(monkeypatch):
    with TestClient(app) as client:
        headers = client.get("/api/health").headers
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["referrer-policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in headers["content-security-policy"]
        assert "content-security-policy" not in client.get("/docs").headers

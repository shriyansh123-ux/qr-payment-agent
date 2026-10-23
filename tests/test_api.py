"""API contract tests using local same-currency requests (no network required)."""
from fastapi.testclient import TestClient
from src.api.server import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200 and res.json()["status"] == "ok"


def test_authenticated_scan(monkeypatch):
    key = "local-testing-secret-key-at-least-24-characters"
    monkeypatch.setenv("QR_API_KEY", key)
    with TestClient(app) as client:
        unauthorized = client.post("/api/scan-text", json={"qr_payload": "upi://pay?pa=demo@upi&am=100&cu=INR"})
        assert unauthorized.status_code == 401
        result = client.post("/api/scan-text", headers={"X-API-Key": key},
                             json={"qr_payload": "upi://pay?pa=demo@upi&am=100&cu=INR"})
        # Risk normalization may require live USD FX, but this is optional.
        assert result.status_code == 200
        data = result.json()
        assert data["success"]
        assert data["qr_info"]["merchant_id"] == "demo@upi"
        assert data["fx_result"]["total_home"] == 100
        assert data["fx_result"]["fee_status"] == "not_quoted"


def test_history_contract(monkeypatch):
    key = "local-testing-secret-key-at-least-24-characters"
    monkeypatch.setenv("QR_API_KEY", key)
    with TestClient(app) as client:
        result = client.get("/api/history", headers={"X-API-Key": key})
        assert result.status_code == 200
        assert "items" in result.json()

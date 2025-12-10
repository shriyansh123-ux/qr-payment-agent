# tests/test_api.py

from fastapi.testclient import TestClient
from src.api.server import app


client = TestClient(app)


def test_health_endpoint():
    """
    Basic health check to ensure the API is up.
    """
    resp = client.get("/api/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("status") == "ok"
    assert "time" in data


def test_scan_text_basic_jpy_to_inr():
    """
    End-to-end test for /api/scan-text.

    This should work EVEN IF GEMINI_API_KEY is missing or invalid,
    because the orchestrator falls back to a deterministic breakdown.
    """
    payload = {
        "user_id": "user-123",
        "qr_payload": "QR:JP:JPY:1500",
        "session_id": ""
    }

    resp = client.post("/api/scan-text", json=payload)
    assert resp.status_code == 200

    data = resp.json()

    # We structured server.py to return this shape:
    # {
    #   "success": True,
    #   "session_id": "...",
    #   "qr_info": {...},
    #   "fx_result": {...},
    #   "risk_result": {...},
    #   "message": "..."
    # }
    assert data.get("success") is True
    assert "session_id" in data
    assert "qr_info" in data
    assert "fx_result" in data
    assert "risk_result" in data
    assert "message" in data

    fx = data["fx_result"]
    assert fx["from_currency"] == "JPY"
    assert fx["to_currency"] == "INR"
    assert isinstance(fx["total_home"], (int, float))


def test_history_endpoint_after_scan():
    """
    After calling /api/scan-text at least once,
    /api/history should contain at least one item.
    """
    # First ensure at least one scan has been done
    payload = {
        "user_id": "user-123",
        "qr_payload": "QR:JP:JPY:1500",
        "session_id": ""
    }
    client.post("/api/scan-text", json=payload)

    # Now call /api/history
    resp = client.get("/api/history")
    assert resp.status_code == 200

    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1

    # Check structure of a single history item
    item = data["items"][-1]
    assert "timestamp" in item
    assert "mode" in item
    assert "input_repr" in item
    assert "home_currency" in item
    assert "total_home" in item
    assert "risk_level" in item
    assert "note" in item

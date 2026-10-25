"""Currency choices propagate through text, image and private saved scans."""
from io import BytesIO

import pytest
import qrcode
from fastapi.testclient import TestClient

from src.api.server import app

KEY = "synthetic-home-currency-testing-key-12345"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    monkeypatch.setattr("src.api.currency_converter.supported_currencies",
                        lambda: [{"code": "INR"}, {"code": "USD"}, {"code": "EUR"}])
    def fx(self, amount_local, local_currency, home_currency):
        return {"from_currency": local_currency, "to_currency": home_currency,
                "total_home": float(amount_local) * 2, "rate": 2,
                "rate_date": "2026-10-25", "provider": "synthetic-test"}
    monkeypatch.setattr("src.agents.fx_rate_agent.FXRateAgent.handle", fx)
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("payload,total", [("QR:JP:JPY:1500", 3000),
                                          ("QR:JP:JPY:1500,QR:US:USD:12", 3024)])
def test_selected_currency_preserves_qr_source(client, payload, total):
    response = client.post("/api/scan-text", headers={"X-API-Key": KEY},
                           json={"qr_payload": payload, "home_currency": "EUR"})
    assert response.status_code == 200, response.text
    data = response.json()
    first = data["items"][0] if data.get("multiple") else data
    assert first["qr_info"]["currency"] == "JPY"
    assert first["qr_info"]["amount"] == 1500
    assert first["fx_result"]["to_currency"] == "EUR"
    assert (data.get("total_home") or first["fx_result"]["total_home"]) == total
    if data.get("multiple"):
        assert data["home_currency"] == "EUR"
    # An explicit currency must not mutate the shared demo user's default.
    default = client.post("/api/scan-text", headers={"X-API-Key": KEY},
                          json={"qr_payload": "QR:IN:INR:1"}).json()
    assert default["fx_result"]["to_currency"] == "INR"


@pytest.mark.parametrize("currency", ["ZZZ", "usd", "", "US", "USD<script>"])
def test_invalid_currency_is_rejected(client, currency):
    response = client.post("/api/scan-text", headers={"X-API-Key": KEY},
                           json={"qr_payload": "QR:JP:JPY:1500", "home_currency": currency})
    assert response.status_code == 422


def test_camera_photo_uses_selected_currency(client):
    image = BytesIO()
    qrcode.make("QR:JP:JPY:1500").save(image, format="PNG")
    response = client.post("/api/scan-image?home_currency=USD", headers={"X-API-Key": KEY},
                           files={"file": ("camera.png", image.getvalue(), "image/png")})
    assert response.status_code == 200, response.text
    assert response.json()["fx_result"]["to_currency"] == "USD"
    assert response.json()["qr_info"]["currency"] == "JPY"


def test_saved_summary_uses_selected_currency(client, monkeypatch, tmp_path):
    monkeypatch.setenv("QR_DATABASE_URL", "sqlite:///" + str(tmp_path / "accounts.sqlite"))
    monkeypatch.setenv("QR_ALLOW_REGISTRATION", "true")
    credentials = {"email": "currency@example.invalid", "password": "synthetic-test-password-1234"}
    assert client.post("/api/account/register", json=credentials).status_code == 201
    login = client.post("/api/account/login", json=credentials).json()
    headers = {"Authorization": "Bearer " + login["access_token"]}
    response = client.post("/api/account/scan-text", headers=headers,
                           json={"qr_payload": "QR:JP:JPY:1500", "home_currency": "USD"})
    assert response.status_code == 200, response.text
    rows = client.get("/api/account/history", headers=headers).json()["items"]
    assert rows[0]["currency"] == "USD"
    assert float(rows[0]["total_home"]) == 3000
    assert "JPY:1500" not in str(rows)


def test_catalog_outage_has_clear_error_but_default_still_works(client, monkeypatch):
    from src.agents.fx_rate_agent import FXUnavailable
    def unavailable():
        raise FXUnavailable("Supported currency list is temporarily unavailable. Try again.")
    monkeypatch.setattr("src.api.currency_converter.supported_currencies", unavailable)
    response = client.post("/api/scan-text", headers={"X-API-Key": KEY},
                           json={"qr_payload": "QR:IN:INR:1", "home_currency": "USD"})
    assert response.status_code == 503
    response = client.post("/api/scan-text", headers={"X-API-Key": KEY},
                           json={"qr_payload": "QR:IN:INR:1"})
    assert response.status_code == 200

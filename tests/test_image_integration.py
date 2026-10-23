"""Image decoding, auth and upload integration tests with no external calls."""
from decimal import Decimal
from io import BytesIO

import cv2
import numpy as np
import qrcode
import pytest
from fastapi.testclient import TestClient

from src.agents.qr_image_agent import QRImageAgent
from src.api.server import app, orchestrator
from src.tools import decode_qr_image_tool

KEY = "local-test-only-key-at-least-twenty-four-characters"


def _png(payload):
    buf = BytesIO()
    qrcode.make(payload, box_size=10, border=4).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    monkeypatch.setattr(orchestrator.fx_agent, "usd_equivalent", lambda amount, cur: Decimal("10"))
    monkeypatch.setattr("src.orchestration.orchestrator_agent.call_gemini",
                        lambda prompt: "Demo reference amount only, recipient unverified.")
    with TestClient(app) as c:
        yield c


def test_decode_real_qr_image(tmp_path):
    path = tmp_path / "upi.png"
    path.write_bytes(_png("upi://pay?pa=merchant@upi&am=100&cu=INR"))
    text = QRImageAgent().handle(str(path))
    assert text == "upi://pay?pa=merchant@upi&am=100&cu=INR"


def test_authenticated_png_upload_end_to_end(client):
    content = _png("upi://pay?pa=merchant@upi&am=100&cu=INR")
    response = client.post("/api/scan-image",
                           headers={"X-API-Key": KEY},
                           files={"file": ("qr.png", content, "image/png")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["success"] is True
    assert result["qr_info"]["merchant_id"] == "merchant@upi"
    assert result["fx_result"]["total_home"] == 100


def test_reject_missing_key(client):
    response = client.post("/api/scan-image",
                           files={"file": ("qr.png", _png("QR:JP:JPY:1500"), "image/png")})
    assert response.status_code == 401


@pytest.mark.parametrize("content,mime,status", [
    (b"not an image", "image/png", 422),
    (b"hello", "text/plain", 415),
    (b"x" * (3 * 1024 * 1024 + 1), "image/png", 413),
])
def test_bad_images_rejected(client, content, mime, status):
    response = client.post("/api/scan-image",
                           headers={"X-API-Key": KEY},
                           files={"file": ("file", content, mime)})
    assert response.status_code == status


def test_multi_qr_image_agent_preserves_newlines(monkeypatch):
    monkeypatch.setattr("src.agents.qr_image_agent.decode_qr_image",
                        lambda path: "QR:JP:JPY:1500\nQR:US:USD:12")
    assert "\n" in QRImageAgent().handle("unused.png")


def test_single_decode_fallback_after_empty_multi(monkeypatch):
    monkeypatch.setattr(decode_qr_image_tool.cv2, "imread",
                        lambda _: np.zeros((200, 200, 3), dtype=np.uint8))
    class Detector:
        def detectAndDecodeMulti(self, img):
            return False, (), None, ()
        def detectAndDecode(self, img):
            return "QR:JP:JPY:1500", None, None
    monkeypatch.setattr(decode_qr_image_tool.cv2, "QRCodeDetector", Detector)
    assert decode_qr_image_tool.decode_qr_image("fake.png") == "QR:JP:JPY:1500"

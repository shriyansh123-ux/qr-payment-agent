"""Image decoding, auth and upload integration tests with no external calls."""
from io import BytesIO

import numpy as np
import pytest
import qrcode
from fastapi.testclient import TestClient

from src.api.server import app
from src.parsers import qr_image
from src.parsers.qr_image import decode_qr_image

KEY = "local-test-only-key-at-least-twenty-four-characters"


def _png(payload):
    buf = BytesIO()
    qrcode.make(payload, box_size=10, border=4).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    with TestClient(app) as c:
        yield c


def test_decode_real_qr_image():
    assert decode_qr_image(_png("upi://pay?pa=merchant@upi&am=100&cu=INR")) == \
        "upi://pay?pa=merchant@upi&am=100&cu=INR"


def test_authenticated_png_upload_end_to_end(client):
    response = client.post("/api/scan-image", headers={"X-API-Key": KEY},
                           files={"file": ("qr.png", _png("upi://pay?pa=merchant@upi&am=100&cu=INR"), "image/png")})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["success"] is True
    assert result["qr_info"]["merchant_id"] == "merchant@upi"
    assert result["fx_result"]["total_home"] == 100


def test_image_upload_requires_key_even_in_public_demo(client, monkeypatch):
    monkeypatch.setenv("QR_PUBLIC_DEMO", "true")
    response = client.post("/api/scan-image",
                           files={"file": ("qr.png", _png("QR:JP:JPY:1500"), "image/png")})
    assert response.status_code == 401


@pytest.mark.parametrize("content,mime,status", [
    (b"not an image", "image/png", 422),
    (b"hello", "text/plain", 415),
    (b"x" * (3 * 1024 * 1024 + 1), "image/png", 413),
])
def test_bad_images_rejected(client, content, mime, status):
    response = client.post("/api/scan-image", headers={"X-API-Key": KEY},
                           files={"file": ("file", content, mime)})
    assert response.status_code == status


def test_multiple_codes_are_newline_separated(monkeypatch):
    class Detector:
        def detectAndDecodeMulti(self, img):
            return True, ("QR:JP:JPY:1500", "QR:US:USD:12"), None, ()

    monkeypatch.setattr(qr_image.cv2, "QRCodeDetector", Detector)
    assert decode_qr_image(_png("unused")) == "QR:JP:JPY:1500\nQR:US:USD:12"


def test_single_decode_fallback_after_empty_multi(monkeypatch):
    monkeypatch.setattr(qr_image.cv2, "imdecode", lambda *_: np.zeros((200, 200, 3), dtype=np.uint8))

    class Detector:
        def detectAndDecodeMulti(self, img):
            return False, (), None, ()

        def detectAndDecode(self, img):
            return "QR:JP:JPY:1500", None, None

    monkeypatch.setattr(qr_image.cv2, "QRCodeDetector", Detector)
    assert decode_qr_image(b"fake") == "QR:JP:JPY:1500"

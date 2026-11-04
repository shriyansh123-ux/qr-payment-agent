"""Decode QR codes directly from uploaded image bytes (no temporary files)."""
import cv2
import numpy as np

MAX_PIXELS = 12_000_000
MAX_CODES = 10
MAX_TEXT_CHARS = 8192


def decode_qr_image(content: bytes) -> str:
    """Return decoded QR text; multiple codes are joined with newlines."""
    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Image could not be decoded")
    if image.shape[0] * image.shape[1] > MAX_PIXELS:
        raise ValueError("Image exceeds the allowed pixel count")
    detector = cv2.QRCodeDetector()
    text = ""
    try:
        ok, items, _, _ = detector.detectAndDecodeMulti(image)
        if ok and items:
            decoded = [value.strip() for value in items if isinstance(value, str) and value.strip()]
            if len(decoded) > MAX_CODES:
                raise ValueError(f"Maximum {MAX_CODES} QR codes per image")
            # Newlines, not commas, separate codes: UPI URLs may contain commas.
            text = "\n".join(decoded)
    except cv2.error:
        pass
    if not text:
        single, _, _ = detector.detectAndDecode(image)
        text = (single or "").strip()
    if not text:
        raise ValueError("No readable QR code was found in this image")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError("Decoded QR content is too long")
    return text

"""Decode a bounded QR image from a validated image path."""
import cv2


def decode_qr_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image could not be decoded")
    if image.shape[0] * image.shape[1] > 12_000_000:
        raise ValueError("Image exceeds the allowed pixel count")
    detector = cv2.QRCodeDetector()
    text = ""
    try:
        ok, items, _, _ = detector.detectAndDecodeMulti(image)
        if ok and items:
            decoded = [value.strip() for value in items if isinstance(value, str) and value.strip()]
            if len(decoded) > 10:
                raise ValueError("Maximum 10 QR codes per image")
            if decoded:
                # Join demo payloads using a newline; UPI URLs may contain commas.
                text = "\n".join(decoded)
    except cv2.error:
        pass
    if not text:
        text, _, _ = detector.detectAndDecode(image)
        text = (text or "").strip()
    if not text:
        raise ValueError("No readable QR code was found in this image")
    if len(text) > 8192:
        raise ValueError("Decoded QR content is too long")
    return text

"""QR image agent: preserve separators between multiple decoded payment QRs."""
from src.tools.decode_qr_image_tool import decode_qr_image


class QRImageAgent:
    def handle(self, image_path: str) -> str:
        payload = decode_qr_image(image_path)
        if not isinstance(payload, str):
            raise ValueError("QR image decoder did not return text")
        # Important: do not remove newlines. They separate QR payloads.
        return payload.strip()

from src.tools.decode_qr_image_tool import decode_qr_image

class QRImageAgent:
    def handle(self, image_path: str) -> str:
        payload = decode_qr_image(image_path)
        if not isinstance(payload, str):
            payload = str(payload)

        # Normalize
        payload = payload.strip()
        payload = payload.replace("\n", "").replace("\r", "").strip()

        return payload

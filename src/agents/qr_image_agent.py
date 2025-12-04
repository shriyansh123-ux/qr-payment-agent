from src.tools.decode_qr_image_tool import decode_qr_image


class QRImageAgent:
    """
    Agent that decodes QR codes from an image.

    Returns:
        list[str]: list of decoded QR payload strings.
    """

    def handle(self, image_path: str):
        texts = decode_qr_image(image_path)
        if not texts:
            raise ValueError("No QR text decoded from image.")
        # Always return a list; orchestrator decides how to handle 1 vs many
        return texts

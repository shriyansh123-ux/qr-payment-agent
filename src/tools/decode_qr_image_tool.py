import os
import cv2


def ensure_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File does not exist: {path}")
    return path


def decode_qr_image(image_path: str):
    """
    Decodes one or multiple QR codes from an image using OpenCV.
    Returns a list of decoded text payloads (e.g. ["QR:JP:JPY:1500", "QR:US:USD:12"]).
    Raises ValueError if no QR is found.
    """
    # 1 — Check file exists
    ensure_file(image_path)

    # 2 — Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at: {image_path}")

    detector = cv2.QRCodeDetector()

    # 3 — Try multi-QR decode (newer OpenCV)
    try:
        # detectAndDecodeMulti returns: retval, decoded_info, points, straight_qrcode
        retval, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
        if retval and decoded_info:
            texts = [s for s in decoded_info if s]
            if texts:
                return texts
    except Exception:
        # Some OpenCV builds don't have detectAndDecodeMulti; fall back below
        pass

    # 4 — Fallback: single QR
    data, points, _ = detector.detectAndDecode(img)
    if data:
        return [data]

    # 5 — Nothing found
    raise ValueError("No QR code detected in the image. Try a clearer or higher-resolution QR.")

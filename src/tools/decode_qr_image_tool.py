# src/tools/decode_qr_image_tool.py
from __future__ import annotations

from typing import Any, List, Optional, Union

import cv2


def _normalize_decoded(decoded: Any) -> str:
    """
    cv2 QRCodeDetector can return:
      - a string
      - empty string / None
      - list of strings (depending on your wrapper / older code)
    We normalize everything into a single QR payload string.
    """
    if decoded is None:
        return ""

    # If already a clean string
    if isinstance(decoded, str):
        return decoded.strip()

    # If list/tuple -> join
    if isinstance(decoded, (list, tuple)):
        parts = []
        for x in decoded:
            if x is None:
                continue
            if isinstance(x, str) and x.strip():
                parts.append(x.strip())
            else:
                s = str(x).strip()
                if s:
                    parts.append(s)
        return ",".join(parts)

    # Fallback
    return str(decoded).strip()


def decode_qr_image(image_path: str) -> str:
    """
    Decode QR payload(s) from an image using OpenCV.
    Returns a string payload.
    If multiple QRs are detected, returns comma-separated payloads.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    detector = cv2.QRCodeDetector()

    # OpenCV has different APIs depending on version:
    # - detectAndDecodeMulti returns (ok, decoded_info, points, straight_qrcode)
    # - detectAndDecode returns (data, points, straight_qrcode)
    payload = ""

    try:
        ok, decoded_info, points, _ = detector.detectAndDecodeMulti(img)
        if ok and decoded_info:
            payload = _normalize_decoded(decoded_info)
    except Exception:
        # fallback to single decode
        data, _, _ = detector.detectAndDecode(img)
        payload = _normalize_decoded(data)

    # Final cleanup
    payload = payload.strip()

    # Some decoders return "['QR:JP:JPY:1500']" like strings — clean that too.
    if payload.startswith("[") and payload.endswith("]"):
        # remove brackets and quotes
        payload = payload.strip("[]").strip()
        payload = payload.strip("'\"").strip()

    return payload

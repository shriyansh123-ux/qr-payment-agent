"""Optional Google Gemini explanation client for non-sensitive summaries."""
import os
import re
import time
import requests


class GeminiHTTPError(Exception):
    def __init__(self, message: str, status_code: int = 0, payload: str = ""):
        super().__init__(message)
        self.status_code = status_code
        # Never expose raw upstream response bodies or secret-bearing URLs.
        self.payload = ""


_GEMINI_COOLDOWN_UNTIL = 0.0


def call_gemini(prompt: str) -> str:
    global _GEMINI_COOLDOWN_UNTIL
    now = time.time()
    if now < _GEMINI_COOLDOWN_UNTIL:
        raise GeminiHTTPError("Gemini cooldown active", status_code=429)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiHTTPError("Missing GEMINI_API_KEY", status_code=401)

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", model):
        raise GeminiHTTPError("Invalid Gemini model identifier")

    # Header-based authentication avoids secrets in URLs and request logs.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, json=payload, headers={"x-goog-api-key": api_key},
                             timeout=(5, 25))
    except requests.RequestException as exc:
        raise GeminiHTTPError("Gemini network request failed") from None

    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After")
        try:
            delay = max(1, min(60, int(retry_after)))
        except (TypeError, ValueError):
            delay = 20
        _GEMINI_COOLDOWN_UNTIL = time.time() + delay
        raise GeminiHTTPError("Gemini rate limit reached", 429)

    if resp.status_code >= 400:
        raise GeminiHTTPError(f"Gemini HTTP error {resp.status_code}", resp.status_code)

    try:
        data = resp.json()
        message = data["candidates"][0]["content"]["parts"][0]["text"]
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Missing Gemini text")
        return message[:6000]
    except (ValueError, KeyError, IndexError, TypeError):
        raise GeminiHTTPError("Gemini response parsing failed", resp.status_code) from None

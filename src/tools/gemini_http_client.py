import os
import time
import requests


class GeminiHTTPError(Exception):
    def __init__(self, message: str, status_code: int = 0, payload: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


# Simple global cooldown to avoid repeated 429 spam
_GEMINI_COOLDOWN_UNTIL = 0.0


def call_gemini(prompt: str) -> str:
    global _GEMINI_COOLDOWN_UNTIL

    # If we're in cooldown window, skip calling Gemini
    now = time.time()
    if now < _GEMINI_COOLDOWN_UNTIL:
        raise GeminiHTTPError("Gemini cooldown active (skipping call)", status_code=429)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise GeminiHTTPError("Missing GEMINI_API_KEY", status_code=401)

    # You can change model if you want
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
    except requests.RequestException as e:
        raise GeminiHTTPError(f"Gemini request failed: {e}", status_code=0)

    if resp.status_code == 429:
        # Backoff: set cooldown for ~20 seconds (or use Retry-After if present)
        retry_after = resp.headers.get("Retry-After")
        delay = 20
        if retry_after:
            try:
                delay = int(retry_after)
            except Exception:
                pass
        _GEMINI_COOLDOWN_UNTIL = time.time() + delay
        raise GeminiHTTPError(f"Gemini HTTP error 429 (quota/rate limit). Cooling down {delay}s.", 429, resp.text)

    if resp.status_code >= 400:
        raise GeminiHTTPError(f"Gemini HTTP error {resp.status_code}", resp.status_code, resp.text)

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        raise GeminiHTTPError("Gemini response parsing failed", resp.status_code, resp.text)

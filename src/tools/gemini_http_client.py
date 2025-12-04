import os
import requests
from typing import Optional

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Default model – you can change this once you know what your key supports
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")



class GeminiHTTPError(Exception):
    pass


def call_gemini(prompt: str, model: Optional[str] = None) -> str:
    """
    Call Gemini via the official HTTP v1 endpoint using requests.
    Returns the response text, or raises GeminiHTTPError on failure.
    """
    api_key = GEMINI_API_KEY
    if not api_key:
        raise GeminiHTTPError("GEMINI_API_KEY environment variable is not set.")

    model_name = model or GEMINI_MODEL
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"

    headers = {
        "Content-Type": "application/json",
    }
    params = {
        "key": api_key
    }
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    resp = requests.post(url, headers=headers, params=params, json=body)
    if resp.status_code != 200:
        raise GeminiHTTPError(
            f"Gemini HTTP error {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    # Extract the text from the first candidate
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        raise GeminiHTTPError(
            f"Unexpected response format from Gemini: {data}"
        ) from e

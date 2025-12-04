from src.tools.gemini_http_client import call_gemini

if __name__ == "__main__":
    print("Using model: gemini-2.5-flash")
    text = call_gemini("Say a short hello message for testing.", model="gemini-2.5-flash")
    print("Model response:\n", text)

import os

# Main model – we KNOW your key supports gemini-2.5-flash
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Default home currency
HOME_CURRENCY = os.getenv("HOME_CURRENCY", "INR")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

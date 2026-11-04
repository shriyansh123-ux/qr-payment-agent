import logging
import os

HOME_CURRENCY = os.getenv("HOME_CURRENCY", "INR")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

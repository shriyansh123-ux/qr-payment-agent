"""Command-line estimate: python -m src.cli"""
from pathlib import Path

from src.config import setup_logging
from src.services.estimator import CostEstimator


def main() -> None:
    setup_logging()
    estimator = CostEstimator()
    print("=== Travel QR Cost Estimator ===")
    mode = input("Scan a text QR or an image QR? (t/i): ").strip().lower()
    if mode == "i":
        path = Path(input("Path to the QR image file: ").strip())
        result = estimator.estimate_image(path.read_bytes())
    else:
        result = estimator.estimate_text(input("Paste QR payload (e.g. QR:JP:JPY:1500): ").strip())
    print("\n" + result["message"])


if __name__ == "__main__":
    main()

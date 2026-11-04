"""Turns QR payloads into dated reference cost estimates. Never makes payments."""
from decimal import Decimal

from src.config import HOME_CURRENCY
from src.parsers.qr_image import decode_qr_image
from src.parsers.qr_text import QRParser
from src.services import currencies
from src.services.fx import FXRateService


class CostEstimator:
    def __init__(self, default_currency: str = HOME_CURRENCY):
        self.default_currency = default_currency
        self.parser = QRParser()
        self.fx = FXRateService()

    def estimate_text(self, qr_payload: str, home_currency: str | None = None) -> dict:
        items = self.parser.parse(qr_payload)
        if home_currency is not None and home_currency not in currencies.supported_codes():
            raise ValueError("Choose a home currency from the supported list.")
        home = home_currency or self.default_currency
        results = [{"qr_info": item,
                    "fx_result": self.fx.convert(item["amount"], item["currency"], home)}
                   for item in items]
        total = sum((r["fx_result"]["total_home"] for r in results), Decimal(0))
        message = (f"Reference conversion before provider fees: {total} {home}. "
                   "This app does not make payments.")
        if len(results) > 1:
            return {"multiple": True, "count": len(results), "items": results,
                    "total_home": total, "home_currency": home, "message": message}
        return {**results[0], "message": message}

    def estimate_image(self, content: bytes, home_currency: str | None = None) -> dict:
        return self.estimate_text(decode_qr_image(content), home_currency)

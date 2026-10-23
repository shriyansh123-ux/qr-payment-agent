"""Strict demo QR and amount-bearing UPI payload validation."""
import pytest
from src.agents.qr_parser_agent import QRParserAgent


def test_demo_qr():
    qr = QRParserAgent().handle("QR:JP:JPY:1500")
    assert qr["amount"] == 1500.0
    assert qr["country"] == "JP"
    assert qr["merchant_id"] is None


def test_multiple_demo_qrs():
    result = QRParserAgent().handle("QR:JP:JPY:1500,QR:US:USD:12")
    assert result["multiple"] and result["count"] == 2


def test_upi():
    qr = QRParserAgent().handle("upi://pay?pa=merchant@upi&am=10&cu=INR")
    assert qr["merchant_id"] == "merchant@upi"
    assert qr["merchant_verified"] is False


@pytest.mark.parametrize("payload", ["QR:JP:JPY:-1", "QR:JP:JPY:0", "QR:JP:JPY:12more", "QR:JP:JPY:1.2.3"])
def test_reject_bad_amount(payload):
    with pytest.raises(ValueError):
        QRParserAgent().handle(payload)

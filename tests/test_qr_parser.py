"""Strict demo QR and amount-bearing UPI payload validation."""
import pytest

from src.parsers.qr_text import QRParser


def parse_one(payload):
    [item] = QRParser().parse(payload)
    return item



def test_demo_qr():
    qr = parse_one("QR:JP:JPY:1500")
    assert qr["amount"] == 1500.0
    assert qr["country"] == "JP"
    assert qr["merchant_id"] is None


def test_multiple_demo_qrs():
    items = QRParser().parse("QR:JP:JPY:1500,QR:US:USD:12")
    assert [i["currency"] for i in items] == ["JPY", "USD"]


def test_upi():
    qr = parse_one("upi://pay?pa=merchant@upi&am=10&cu=INR")
    assert qr["merchant_id"] == "merchant@upi"
    assert qr["merchant_verified"] is False


@pytest.mark.parametrize("payload", ["QR:JP:JPY:-1", "QR:JP:JPY:0", "QR:JP:JPY:12more", "QR:JP:JPY:1.2.3"])
def test_reject_bad_amount(payload):
    with pytest.raises(ValueError):
        parse_one(payload)

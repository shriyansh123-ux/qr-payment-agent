"""Synthetic EMV merchant-presented QR checks; never real financial records."""
import pytest
from src.agents.emv_parser import crc16_ccitt
from src.agents.qr_parser_agent import QRParserAgent


def tlv(tag, value):
    return f"{tag}{len(value):02d}{value}"


def sample_emv(currency="392", amount="1500"):
    account = tlv("00", "com.example.demo") + tlv("01", "synthetic")
    root = (
        tlv("00", "01") + tlv("01", "12") + tlv("26", account)
        + tlv("52", "0000") + tlv("53", currency) + tlv("54", amount)
        + tlv("58", "JP") + tlv("59", "Sample Shop") + tlv("60", "Tokyo")
        + "6304"
    )
    return root + crc16_ccitt(root)


def test_emv_jpy_amount():
    result = QRParserAgent().handle(sample_emv())
    assert result["amount"] == 1500
    assert result["currency"] == "JPY"
    assert result["merchant_verified"] is False
    assert result["merchant_id"] is None
    assert result["raw_fields"]["scheme"] == "emv-mpm"


def test_emv_crc_detects_tampering():
    data = sample_emv()
    with pytest.raises(ValueError, match="CRC"):
        QRParserAgent().handle(data[:-4] + "0000")


def test_emv_rejects_missing_amount_even_with_valid_crc():
    value = sample_emv()
    # Create structurally valid no-amount QR with recalculated CRC.
    raw = value[:value.index("54041500")] + value[value.index("54041500")+8:-4]
    with pytest.raises(ValueError, match="mandatory"):
        QRParserAgent().handle(raw + crc16_ccitt(raw))


def test_emv_rejects_unknown_currency():
    with pytest.raises(ValueError, match="currency"):
        QRParserAgent().handle(sample_emv(currency="999"))


def test_emv_rejects_duplicate_root_tag():
    raw = sample_emv()
    raw = raw[:-8] + tlv("53", "392") + "6304"
    with pytest.raises(ValueError, match="Duplicate"):
        QRParserAgent().handle(raw + crc16_ccitt(raw))


def test_emv_rejects_invalid_nested_fields():
    root = sample_emv()
    broken = root.replace("com.example.demo", "xxxxxxxxxxxxxxxx")
    with pytest.raises(ValueError):
        QRParserAgent().handle(broken)


def test_emv_rejects_fractional_jpy():
    with pytest.raises(ValueError, match="JPY"):
        QRParserAgent().handle(sample_emv(amount="1500.50"))

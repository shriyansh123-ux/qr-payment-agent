"""Restricted, validate-first EMVCo merchant-presented QR (MMP) interpreter.

Supports amount-bearing payloads for a limited documented ISO 4217 set.
Checks CRC-16/CCITT-FALSE and mandatory root fields; a matching checksum
is *not* authentication or evidence of a trustworthy merchant.
"""
import re

# ISO 4217 numeric currency codes, a consciously limited supported subset.
CURRENCIES = {
    "036": "AUD", "124": "CAD", "156": "CNY", "344": "HKD",
    "356": "INR", "392": "JPY", "410": "KRW", "458": "MYR",
    "702": "SGD", "764": "THB", "826": "GBP", "840": "USD",
    "978": "EUR", "986": "BRL",
}


def crc16_ccitt(data):
    crc = 0xFFFF
    for octet in data.encode("utf-8"):
        crc ^= octet << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xFFFF
    return f"{crc:04X}"


def parse_tlv(payload):
    fields, offset = {}, 0
    while offset < len(payload):
        if offset + 4 > len(payload):
            raise ValueError("Incomplete EMV QR TLV header")
        tag, length_text = payload[offset:offset+2], payload[offset+2:offset+4]
        if not (tag.isascii() and tag.isdecimal() and
                length_text.isascii() and length_text.isdecimal()):
            raise ValueError("Invalid EMV QR TLV tag or length")
        length = int(length_text)
        if not 1 <= length <= 99 or offset + 4 + length > len(payload):
            raise ValueError("Invalid or truncated EMV QR TLV field")
        if tag in fields:
            raise ValueError("Duplicate EMV QR TLV tag")
        value = payload[offset+4:offset+4+length]
        fields[tag] = value
        offset += 4 + length
    return fields


def parse_emv_qr(payload):
    fields = parse_tlv(payload)
    if not payload.startswith("000201") or fields.get("00") != "01":
        raise ValueError("EMV QR payload indicator must be 01")
    if "01" in fields and fields["01"] not in ("11", "12"):
        raise ValueError("Invalid EMV QR initiation method")
    # CRC tag must be the last tag and CRC covers its own tag + length.
    if not re.search(r"6304[0-9A-Fa-f]{4}$", payload):
        raise ValueError("Missing terminal EMV QR CRC")
    if crc16_ccitt(payload[:-4]) != fields["63"].upper():
        raise ValueError("Invalid EMV QR CRC")
    required = ("52", "53", "54", "58", "59", "60")
    if any(tag not in fields for tag in required):
        raise ValueError("EMV QR missing mandatory fields or amount")
    if not any(f"{tag:02d}" in fields for tag in range(2, 52)):
        raise ValueError("EMV QR missing merchant account information")
    if not re.fullmatch(r"\d{4}", fields["52"]):
        raise ValueError("Invalid EMV QR merchant category")
    currency = CURRENCIES.get(fields["53"])
    if currency is None:
        raise ValueError("Unsupported EMV QR numeric currency")
    country = fields["58"]
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("Invalid EMV QR country")
    if not (1 <= len(fields["59"]) <= 25 and 1 <= len(fields["60"]) <= 15):
        raise ValueError("Invalid EMV QR merchant name or city")
    # Merchant templates 26-51 contain nested TLVs with a scheme identifier.
    for tag in range(26, 52):
        value = fields.get(f"{tag:02d}")
        if value is not None:
            nested = parse_tlv(value)
            if "00" not in nested or not nested["00"]:
                raise ValueError("EMV QR merchant template lacks scheme identifier")
    return {
        "country": country, "currency": currency, "amount_raw": fields["54"],
        "merchant_name_claim": fields["59"],
    }

# tests/test_qr_parser.py

from src.agents.qr_parser_agent import QRParserAgent


def test_basic_qr_parsing():
    agent = QRParserAgent()

    payload = "QR:JP:JPY:1500"
    result = agent.handle(payload)

    # basic structure
    assert isinstance(result, dict)

    # Required fields
    assert result["country"] == "JP"
    assert result["currency"] == "JPY"
    assert result["amount"] == 1500.0
    assert "merchant_id" in result

    # Optional: if you *do* add raw info in future, it won't break this test
    # We just check that if raw_fields exists, it has "raw" inside
    if "raw_fields" in result:
        assert isinstance(result["raw_fields"], dict)
        assert "raw" in result["raw_fields"]

"""Compatibility helper: no fabricated QR data on decode failure."""
from src.agents.qr_parser_agent import QRParserAgent


def decode_qr(payload: str) -> dict:
    return QRParserAgent().handle(payload)

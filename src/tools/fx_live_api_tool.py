"""Compatibility helper; no silent None or fictitious rates."""
from src.agents.fx_rate_agent import FXRateAgent


def get_live_fx_rate(from_currency: str, to_currency: str):
    rate, _, _ = FXRateAgent().get_rate(from_currency, to_currency)
    return float(rate)

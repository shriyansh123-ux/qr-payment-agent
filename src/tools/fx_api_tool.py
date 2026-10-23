"""Compatibility helper to obtain a verified reference rate."""
from src.agents.fx_rate_agent import FXRateAgent


def get_fx_rate(from_currency, to_currency):
    rate, observed, source = FXRateAgent().get_rate(from_currency, to_currency)
    return {"rate": float(rate), "rate_date": observed, "provider": source}

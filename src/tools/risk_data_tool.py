"""Compatibility helper using normalized USD amount, not country stereotypes."""
from src.agents.risk_scorer import RiskScorer


def assess_risk(merchant_id: str, country: str, amount: float, amount_usd=None):
    return RiskScorer().evaluate(merchant_id, country, amount, amount_usd)

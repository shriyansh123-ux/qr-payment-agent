"""Heuristic caution does not assert merchant authenticity or country fraud risk."""
from src.agents.risk_scorer import RiskScorer


def test_unknown_normalization_is_not_assessed():
    result = RiskScorer().evaluate(None, "JP", 500)
    assert result["risk_level"] == "not_assessed"
    assert result["risk_score"] is None


def test_high_normalized_value():
    result = RiskScorer().evaluate("unverified@upi", "IN", 150000, amount_usd=2000)
    assert result["risk_level"] == "high"
    assert any("High-value" in x for x in result["reasons"])


def test_small_normalized_value():
    result = RiskScorer().evaluate(None, "JP", 1000, amount_usd=7)
    assert result["risk_level"] in ("low", "medium")

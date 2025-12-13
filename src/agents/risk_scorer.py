from typing import Dict, Any, List


class RiskScorer:
    """
    Explainable risk scoring.
    Score ranges:
    - 0 to 30: low
    - 31 to 65: medium
    - 66+: high
    """

    def __init__(self, memory=None):
        self.memory = memory

    def score_amount(self, amount: float, reasons: List[str]) -> float:
        score = 0.0
        if amount >= 5000:
            score += 40
            reasons.append("High amount (>= 5000).")
        elif amount >= 1000:
            score += 20
            reasons.append("Moderate amount (>= 1000).")
        else:
            score += 5
        return score

    def score_country(self, country: str, reasons: List[str]) -> float:
        score = 0.0
        unfamiliar = {"TH", "EU", "RU", "BR", "NG"}  # sample set (adjust later)
        if country.upper() in unfamiliar:
            score += 25
            reasons.append(f"Unfamiliar/high-fraud country pattern: {country.upper()}.")
        else:
            score += 5
        return score

    def score_merchant(self, merchant_id: str, reasons: List[str]) -> float:
        """
        If merchant never seen before in recent history -> add risk.
        """
        score = 0.0
        if self.memory is None or not hasattr(self.memory, "get_recent_merchants"):
            # memory not wired, keep safe default
            reasons.append("Merchant history unavailable; using baseline merchant score.")
            return 10.0

        history = self.memory.get_recent_merchants()
        seen = any(h["merchant_id"] == merchant_id for h in history)

        if not seen:
            score += 20
            reasons.append("Merchant not seen in your recent history.")
        else:
            score += 5
            reasons.append("Merchant seen recently (familiar).")

        return score

    def evaluate(self, merchant_id: str, country: str, amount: float) -> Dict[str, Any]:
        reasons: List[str] = []
        score = 0.0

        score += self.score_amount(amount, reasons)
        score += self.score_country(country, reasons)
        score += self.score_merchant(merchant_id, reasons)

        if score >= 66:
            level = "high"
        elif score >= 31:
            level = "medium"
        else:
            level = "low"

        return {
            "risk_score": float(score),
            "risk_level": level,
            "reasons": reasons,
        }

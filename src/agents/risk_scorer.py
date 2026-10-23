"""Transparent caution indicators, NOT fraud detection or merchant verification."""
from decimal import Decimal, InvalidOperation


class RiskScorer:
    def __init__(self, memory=None):
        self.memory = memory  # retained for call compatibility; not used as proof of trust

    def evaluate(self, merchant_id, country, amount, amount_usd=None):
        reasons = ["QR content does not independently verify the merchant or authorize a payment."]
        score = 20.0  # QR is unverified, even if the same address was seen before
        if not merchant_id:
            reasons.append("No merchant identifier was provided; identity unknown.")
            score += 10
        else:
            reasons.append("Claimed payee identifier is unverified; independently confirm the recipient.")
        if amount_usd is None:
            return {
                "risk_score": None, "risk_level": "not_assessed",
                "reasons": reasons + ["Transaction-size caution not assessed: USD reference rate unavailable."],
            }
        try:
            normalized = Decimal(str(amount_usd))
            if not normalized.is_finite() or normalized <= 0:
                raise ValueError("Invalid normalized amount")
        except (ValueError, InvalidOperation, TypeError) as exc:
            raise ValueError("Invalid USD equivalent") from exc
        if normalized >= Decimal("1000"):
            score += 45
            reasons.append("High-value transaction (at least USD 1,000 equivalent).")
        elif normalized >= Decimal("250"):
            score += 20
            reasons.append("Moderate-value transaction (at least USD 250 equivalent).")
        else:
            reasons.append("Smaller transaction value; this does not establish safety.")
        level = "high" if score >= 65 else "medium" if score >= 35 else "low"
        reasons.append("Heuristic caution only; not a fraud probability or payment recommendation.")
        return {"risk_score": float(score), "risk_level": level, "reasons": reasons}

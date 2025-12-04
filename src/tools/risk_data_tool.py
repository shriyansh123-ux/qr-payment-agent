def assess_risk(merchant_id: str, country: str, amount: float) -> dict:
    """
    Very simple risk heuristic for demo.
    """
    risk = "low"
    reasons = []

    if amount > 50000:
        risk = "medium"
        reasons.append("High transaction amount.")

    if country not in ("JP", "US", "IN"):
        risk = "medium"
        reasons.append("Unfamiliar country for typical user profile.")

    return {"risk_level": risk, "reasons": reasons}

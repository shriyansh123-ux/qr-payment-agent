# src/agents/risk_scorer.py

from typing import List, Dict, Any, Optional


class RiskScorer:
    """
    Stateless heuristic risk scorer.
    It does NOT rely on memory methods like get_recent_merchants(),
    so it is safe to use both in CLI and in the FastAPI server.

    It computes:
      - risk_score (0–100)
      - risk_level: "low" / "medium" / "high"
      - reasons: list of human-readable strings
    """

    def __init__(self, memory: Optional[object] = None):
        # We keep memory for future extensions, but do not depend on it now.
        self.memory = memory

    # ---------- Individual scoring helpers ----------

    def score_amount(self, amount: float, reasons: List[str]) -> float:
        """
        Simple rule:
        - < 5k equivalent -> low risk contribution
        - 5k–50k -> moderate
        - > 50k -> high
        """
        if amount <= 0:
            reasons.append("Amount is zero or negative; unusual transaction.")
            return 20.0

        if amount < 5000:
            return 5.0
        elif amount < 50_000:
            reasons.append("Medium-sized transaction amount.")
            return 20.0
        else:
            reasons.append("High-value transaction amount.")
            return 40.0

    def score_country(self, country: str, reasons: List[str]) -> float:
        """
        Very simple country-based heuristic.
        In real life, you'd connect to a risk DB or config.
        """
        country = (country or "").upper()

        low_risk = {"IN", "US", "JP", "EU", "GB"}
        medium_risk = {"TH", "SG", "AE"}
        high_risk = {"XX", "ZZ"}  # placeholder for unknown / high-risk

        if country in low_risk:
            return 5.0

        if country in medium_risk:
            reasons.append(f"Country {country} is medium risk in default mapping.")
            return 15.0

        if country in high_risk:
            reasons.append(f"Country {country} is high risk in default mapping.")
            return 30.0

        # Unknown country
        reasons.append(f"Country {country or 'UNKNOWN'} is not in known list; treating as medium risk.")
        return 15.0

    def score_merchant(self, merchant_id: str, reasons: List[str]) -> float:
        """
        Very basic merchant heuristic, WITHOUT using memory.

        - Very short or very long merchant IDs are treated as slightly riskier.
        - Otherwise contributes small risk.
        """
        merchant_id = merchant_id or ""

        if len(merchant_id) == 0:
            reasons.append("Missing merchant ID.")
            return 20.0

        if len(merchant_id) < 4:
            reasons.append("Very short merchant ID; could be suspicious.")
            return 15.0

        if len(merchant_id) > 20:
            reasons.append("Unusually long merchant ID.")
            return 10.0

        # Default small contribution
        return 5.0

    # ---------- Main evaluate() method ----------

    def evaluate(self, merchant_id: str, country: str, amount: float) -> Dict[str, Any]:
        """
        Compute overall risk score + label + reasons.
        """
        reasons: List[str] = []
        score = 0.0

        # Combine contribution from each dimension
        score += self.score_amount(amount, reasons)
        score += self.score_country(country, reasons)
        score += self.score_merchant(merchant_id, reasons)

        # Clip to [0, 100]
        score = max(0.0, min(100.0, score))

        # Map numeric score to level
        if score < 30:
            level = "low"
        elif score < 60:
            level = "medium"
        else:
            level = "high"

        # If no reasons were added, add a generic one
        if not reasons:
            reasons.append("Standard risk evaluation; no specific concerns detected.")

        return {
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons,
        }

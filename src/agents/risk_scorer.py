import math
from typing import List, Dict


BAD_MERCHANTS = {"M998", "M777", "MXYZ"}  # example flagged IDs
COUNTRY_DISTANCE = {
    ("IN", "JP"): 1,
    ("IN", "US"): 2,
    ("IN", "BR"): 3,
    ("IN", "TH"): 1,
    ("IN", "EU"): 1,
}

AMOUNT_THRESHOLD = 20000  # INR equivalent


class RiskScorer:
    """
    A multi-signal intelligent risk engine that returns:
    {
       "risk_level": "low/medium/high",
       "score": int,
       "reasons": [...]
    }
    """

    def __init__(self, user_profile: dict, memory_bank):
        self.profile = user_profile
        self.memory = memory_bank

    def score_country(self, country: str, reasons: List[str]) -> int:
        home = "IN"
        dist = COUNTRY_DISTANCE.get((home, country), 2)
        if dist == 3:
            reasons.append("Very distant geographic region.")
        elif dist == 2:
            reasons.append("Foreign region; moderate travel risk.")
        return dist

    def score_amount(self, amount: float, reasons: List[str]) -> int:
        if amount > AMOUNT_THRESHOLD:
            reasons.append("Large transaction amount.")
            return 3
        if amount > (AMOUNT_THRESHOLD / 4):
            reasons.append("Moderate transaction size.")
            return 1
        return 0

    def score_merchant(self, merchant: str, reasons: List[str]) -> int:
        if merchant in BAD_MERCHANTS:
            reasons.append("Merchant flagged for risk.")
            return 3

        history = self.memory.get_recent_merchants()
        if merchant not in history:
            reasons.append("First time interacting with this merchant.")
            return 1
        else:
            reasons.append("Merchant seen before; trusted.")
            return -1

    def risk_level(self, score: int) -> str:
        if score >= 6:
            return "high"
        if score >= 3:
            return "medium"
        return "low"

    def evaluate(self, merchant_id: str, country: str, amount: float):
        reasons = []
        score = 0

        score += self.score_country(country, reasons)
        score += self.score_amount(amount, reasons)
        score += self.score_merchant(merchant_id, reasons)

        level = self.risk_level(score)

        return {
            "risk_level": level,
            "score": score,
            "reasons": reasons,
        }

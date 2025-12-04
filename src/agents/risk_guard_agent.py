from src.agents.risk_scorer import RiskScorer


class RiskGuardAgent:
    def __init__(self, memory_bank=None):
        self.memory = memory_bank

    def handle(self, merchant_id: str, country: str, amount: float):
        scorer = RiskScorer(
            user_profile={},
            memory_bank=self.memory
        )
        return scorer.evaluate(
            merchant_id=merchant_id,
            country=country,
            amount=amount
        )

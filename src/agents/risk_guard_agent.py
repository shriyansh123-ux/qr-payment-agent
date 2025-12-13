from src.agents.risk_scorer import RiskScorer


class RiskGuardAgent:
    def __init__(self, memory=None):
        self.scorer = RiskScorer(memory=memory)

    def handle(self, merchant_id: str, country: str, amount: float):
        return self.scorer.evaluate(
            merchant_id=merchant_id,
            country=country,
            amount=amount,
        )

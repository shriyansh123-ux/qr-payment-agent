from src.agents.risk_scorer import RiskScorer


class RiskGuardAgent:
    def __init__(self, memory=None):
        self.scorer = RiskScorer(memory=memory)

    def handle(self, merchant_id, country, amount, amount_usd=None):
        return self.scorer.evaluate(
            merchant_id=merchant_id,
            country=country,
            amount=amount,
            amount_usd=amount_usd,
        )

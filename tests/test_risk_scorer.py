# tests/test_risk_scorer.py

from src.agents.risk_scorer import RiskScorer


def test_risk_scorer_low_risk_small_amount_jp():
    scorer = RiskScorer()

    res = scorer.evaluate(
        merchant_id="M12345",
        country="JP",
        amount=1000.0,
    )

    assert isinstance(res, dict)
    assert "risk_score" in res
    assert "risk_level" in res
    assert "reasons" in res

    assert isinstance(res["risk_score"], float)
    assert isinstance(res["reasons"], list)
    assert res["risk_level"] in ("low", "medium", "high")

    # for small JP transaction, risk should be on the lower side
    assert res["risk_score"] < 60.0


def test_risk_scorer_high_risk_large_amount_unknown_country():
    scorer = RiskScorer()

    res = scorer.evaluate(
        merchant_id="X",
        country="ZZ",      # we treat this as high/unknown risk
        amount=100000.0,   # large amount
    )

    assert res["risk_level"] in ("medium", "high")
    assert res["risk_score"] >= 30.0
    assert len(res["reasons"]) > 0

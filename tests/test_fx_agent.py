"""Reference FX tests do not call live services."""
from decimal import Decimal
import pytest
from src.agents.fx_rate_agent import FXRateAgent, FXUnavailable


def test_same_currency_is_exact_before_unknown_fees():
    result = FXRateAgent().handle(1500, "INR", "INR")
    assert result["rate"] == 1.0
    assert result["total_home"] == 1500.0
    assert result["fee_status"] == "not_quoted"


def test_mocked_reference_rate(monkeypatch):
    agent = FXRateAgent()
    monkeypatch.setattr(agent, "get_rate", lambda a,b: (Decimal("0.60"), "2026-10-23", "test-reference"))
    result = agent.handle(1500, "JPY", "INR")
    assert result["total_home"] == 900.0
    assert result["rate_date"] == "2026-10-23"


def test_no_fake_rate_if_provider_down(monkeypatch):
    agent = FXRateAgent()
    def fail(*args):
        raise FXUnavailable("unavailable")
    monkeypatch.setattr(agent, "get_rate", fail)
    with pytest.raises(FXUnavailable):
        agent.handle(1500, "JPY", "INR")

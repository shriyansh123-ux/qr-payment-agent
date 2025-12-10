# tests/test_fx_agent.py

from src.agents.fx_rate_agent import FXRateAgent


def test_fx_agent_jpy_to_inr_has_all_fields():
    agent = FXRateAgent()

    result = agent.handle(
        amount_local=1500.0,
        local_currency="JPY",
        home_currency="INR",
    )

    # Must be a dict
    assert isinstance(result, dict)

    # These keys should always exist
    expected_keys = [
        "from_currency",
        "to_currency",
        "rate",
        "base_home",
        "markup_home",
        "network_fee_home",
        "total_home",
        "notes",
        "provider",
    ]
    for key in expected_keys:
        assert key in result, f"Missing key in fx_result: {key}"

    # Basic type sanity checks
    assert result["from_currency"] == "JPY"
    assert result["to_currency"] == "INR"
    assert isinstance(result["rate"], (int, float))
    assert isinstance(result["total_home"], (int, float))

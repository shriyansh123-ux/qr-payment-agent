"""Core estimates need no risk lookups, AI providers or network for same-currency QRs."""
from decimal import Decimal

import pytest

from src.services.estimator import CostEstimator


@pytest.fixture
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Same-currency scans must not call external services")
    monkeypatch.setattr("requests.get", forbidden)
    monkeypatch.setattr("requests.post", forbidden)


def test_same_currency_scan_needs_no_external_requests(offline):
    result = CostEstimator("INR").estimate_text("upi://pay?pa=merchant@upi&am=100&cu=INR")
    assert result["fx_result"]["total_home"] == 100
    assert "risk_result" not in result and "session_id" not in result
    assert "Reference conversion" in result["message"]
    assert "merchant@upi" not in result["message"]


def test_multi_scan_has_only_conversion_results(offline):
    result = CostEstimator("INR").estimate_text("QR:IN:INR:100,QR:IN:INR:200")
    assert result["total_home"] == 300 and result["count"] == 2
    assert all(set(item) == {"qr_info", "fx_result"} for item in result["items"])


def test_amounts_stay_decimal(offline):
    result = CostEstimator("INR").estimate_text("QR:IN:INR:0.10,QR:IN:INR:0.20")
    assert isinstance(result["total_home"], Decimal)
    assert result["total_home"] == Decimal("0.30")  # 0.1 + 0.2 != 0.3 with floats


def test_zero_decimal_target_currency_is_rounded_to_whole_units(monkeypatch):
    estimator = CostEstimator("JPY")
    monkeypatch.setattr(estimator.fx, "get_rate", lambda a, b: (Decimal("1.7368"), "2026-11-03", "test"))
    result = estimator.estimate_text("QR:IN:INR:100")
    assert str(result["fx_result"]["total_home"]) == "174"


def test_three_decimal_target_currency(monkeypatch):
    estimator = CostEstimator("KWD")
    monkeypatch.setattr(estimator.fx, "get_rate", lambda a, b: (Decimal("0.0036789"), "2026-11-03", "test"))
    assert str(estimator.estimate_text("QR:IN:INR:100")["fx_result"]["total_home"]) == "0.368"


@pytest.mark.parametrize("payload", ["QR:JP:JPY:1500.50", "QR:KR:KRW:10.5"])
def test_zero_decimal_source_amounts_must_be_whole(offline, payload):
    with pytest.raises(ValueError, match="whole units"):
        CostEstimator("INR").estimate_text(payload)

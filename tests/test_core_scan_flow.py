"""Core scan calculations do not need risk lookups or an AI provider."""
from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank


def agent():
    memory = SimpleMemoryBank()
    memory.upsert_profile("synthetic-user", {"home_currency": "INR"})
    return OrchestratorAgent(InMemorySessionService(), memory)


def test_same_currency_scan_needs_no_external_requests(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Same-currency scans must not call FX normalization or AI providers")
    monkeypatch.setattr("requests.get", forbidden)
    monkeypatch.setattr("requests.post", forbidden)
    result = agent().handle_qr_scan("synthetic-user", "", "upi://pay?pa=merchant@upi&am=100&cu=INR")
    assert result["fx_result"]["total_home"] == 100
    assert "risk_result" not in result
    assert "Reference conversion" in result["message"]
    assert "merchant@upi" not in result["message"]


def test_multi_scan_has_only_conversion_results(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No external request is needed")
    monkeypatch.setattr("requests.get", forbidden)
    monkeypatch.setattr("requests.post", forbidden)
    result = agent().handle_qr_scan("synthetic-user", "", "QR:IN:INR:100,QR:IN:INR:200")
    assert result["total_home"] == 300
    assert result["count"] == 2
    assert all(set(item) == {"qr_info", "fx_result"} for item in result["items"])

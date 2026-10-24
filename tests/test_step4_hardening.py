"""Step 4 safeguards: in-memory session limits and secret-safe Gemini transport."""
from dataclasses import dataclass

import pytest

from src.orchestration.session_manager import InMemorySessionService
from src.tools import gemini_http_client as gemini


def test_session_count_is_bounded():
    store = InMemorySessionService(max_sessions=2, ttl_seconds=120)
    first = store.create_session()
    second = store.create_session()
    third = store.create_session()
    assert len(store._sessions) == 2
    assert store.get_session(first.session_id) is None
    assert store.get_session(second.session_id) is not None
    assert store.get_session(third.session_id) is not None


def test_idle_sessions_expire(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("src.orchestration.session_manager.time.time", lambda: clock[0])
    store = InMemorySessionService(ttl_seconds=30)
    session = store.create_session()
    clock[0] = 1025.0
    assert store.get_session(session.session_id) is not None
    clock[0] = 1040.0
    assert store.get_session(session.session_id) is not None
    clock[0] = 1071.0
    assert store.get_session(session.session_id) is None


def test_expired_session_is_not_resurrected(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("src.orchestration.session_manager.time.time", lambda: clock[0])
    store = InMemorySessionService(ttl_seconds=30)
    session = store.create_session()
    clock[0] = 1031.0
    store.update_session(session)
    assert store.get_session(session.session_id) is None


def test_configured_key_is_sent_in_gemini_header_not_url(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-sensitive-key-12345")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setattr(gemini, "_GEMINI_COOLDOWN_UNTIL", 0)
    captured = {}
    class Response:
        status_code = 200
        headers = {}
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "Demo only."}]}}]}
    def post(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        return Response()
    monkeypatch.setattr(gemini.requests, "post", post)
    assert gemini.call_gemini("Explain a reference amount") == "Demo only."
    assert "test-sensitive-key" not in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == "test-sensitive-key-12345"


def test_gemini_provider_errors_hide_response_body(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-sensitive-key-12345")
    monkeypatch.setattr(gemini, "_GEMINI_COOLDOWN_UNTIL", 0)
    class Response:
        status_code = 500
        headers = {}
        text = "provider diagnostic containing sensitive text"
    monkeypatch.setattr(gemini.requests, "post", lambda *a, **kw: Response())
    with pytest.raises(gemini.GeminiHTTPError) as result:
        gemini.call_gemini("Test")
    assert "sensitive" not in str(result.value)
    assert result.value.payload == ""

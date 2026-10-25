"""Bounded and expiring in-memory sessions."""


from src.orchestration.session_manager import InMemorySessionService


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

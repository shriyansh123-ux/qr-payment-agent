"""Bounded, time-limited in-process demo sessions.

Single-worker memory only; use a real identity-aware session store before
supporting multiple users or more than one server replica.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from threading import RLock
import uuid
import time


@dataclass
class SessionState:
    session_id: str
    history: List[Dict[str, str]] = field(default_factory=list)
    last_qr_summary: str = ""
    status: str = "IDLE"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


class InMemorySessionService:
    def __init__(self, max_sessions: int = 256, ttl_seconds: int = 1800):
        if max_sessions < 1 or ttl_seconds < 1:
            raise ValueError("Session capacity and expiration must be positive")
        self._sessions: Dict[str, SessionState] = {}
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self._lock = RLock()

    def _prune(self, now: float):
        for sid, state in list(self._sessions.items()):
            if now - state.last_accessed >= self.ttl_seconds:
                del self._sessions[sid]

    def create_session(self) -> SessionState:
        with self._lock:
            now = time.time()
            self._prune(now)
            if len(self._sessions) >= self.max_sessions:
                oldest_id = min(self._sessions, key=lambda k: self._sessions[k].last_accessed)
                del self._sessions[oldest_id]
            sid = str(uuid.uuid4())
            state = SessionState(session_id=sid, created_at=now, last_accessed=now)
            self._sessions[sid] = state
            return state

    def get_session(self, session_id: str):
        with self._lock:
            now = time.time()
            self._prune(now)
            state = self._sessions.get(session_id)
            if state is not None:
                state.last_accessed = now
            return state

    def update_session(self, state: SessionState):
        with self._lock:
            now = time.time()
            self._prune(now)
            # Do not resurrect expired/evicted sessions from a late request.
            if state.session_id in self._sessions:
                state.last_accessed = now
                self._sessions[state.session_id] = state


def compact_history(history: List[Dict[str, str]], max_messages: int = 10):
    if len(history) <= max_messages:
        return history
    compressed = history[-max_messages:]
    compressed.insert(0, {
        "role": "system",
        "content": "(Earlier conversation summarized: multiple QR scans this trip.)"
    })
    return compressed

from dataclasses import dataclass, field
from typing import List, Dict, Any
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


class InMemorySessionService(object):
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def create_session(self) -> SessionState:
        sid = str(uuid.uuid4())
        state = SessionState(session_id=sid)
        self._sessions[sid] = state
        return state

    def get_session(self, session_id: str):
        return self._sessions.get(session_id)

    def update_session(self, state: SessionState):
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

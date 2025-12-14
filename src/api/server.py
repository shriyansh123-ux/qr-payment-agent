import os
import tempfile
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank

# -----------------------------
# App init
# -----------------------------
app = FastAPI(title="QR Payment Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = InMemorySessionService()
memory = SimpleMemoryBank()

# default user profile
DEFAULT_USER_ID = "user-123"
memory.upsert_profile(DEFAULT_USER_ID, {
    "home_currency": "INR",
    "preferred_card": "VISA",
    "risk_preference": "balanced",
})

orchestrator = OrchestratorAgent(sessions, memory)

# -----------------------------
# Request models
# -----------------------------
class ScanTextRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = ""
    qr_payload: str
    user_country: Optional[str] = None  # 👈 NEW


class ScanImageRequest(BaseModel):
    user_id: str = DEFAULT_USER_ID
    session_id: Optional[str] = ""
    user_country: Optional[str] = None  # 👈 NEW


# -----------------------------
# Routes
# -----------------------------
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/scan-text")
def scan_text(req: ScanTextRequest) -> Dict[str, Any]:
    result = orchestrator.handle_qr_scan(
        user_id=req.user_id,
        session_id=req.session_id or "",
        qr_payload=req.qr_payload,
        user_country=req.user_country,  # 👈 NEW
    )
    return result


@app.post("/api/scan-image")
async def scan_image(
    user_id: str = Query(DEFAULT_USER_ID),
    session_id: str = Query(""),
    user_country: Optional[str] = Query(None),  # 👈 NEW
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    # save to temp file
    suffix = os.path.splitext(file.filename or "")[-1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        result = orchestrator.handle_qr_image_scan(
            user_id=user_id,
            session_id=session_id or "",
            image_path=tmp_path,
            user_country=user_country,  # 👈 NEW
        )
        return result
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.get("/api/history")
def history(user_id: str = Query(DEFAULT_USER_ID), session_id: str = Query("")) -> Dict[str, Any]:
    # If your session manager supports it, return actual history.
    # Otherwise, return empty list to avoid breaking UI.
    state = sessions.get_session(session_id) if session_id else None
    if not state:
        return {"user_id": user_id, "session_id": session_id, "history": []}
    return {"user_id": user_id, "session_id": state.session_id, "history": state.history}


@app.post("/api/clear-history")
def clear_history(user_id: str = Query(DEFAULT_USER_ID), session_id: str = Query("")) -> Dict[str, Any]:
    # Simple and safe: clear only current session if exists
    if session_id:
        state = sessions.get_session(session_id)
        if state:
            state.history = []
            sessions.update_session(state)
    return {"ok": True, "user_id": user_id, "session_id": session_id}

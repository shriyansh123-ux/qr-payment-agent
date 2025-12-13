# src/api/server.py
from __future__ import annotations

import logging
import os
import tempfile
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pydantic import BaseModel

from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank
from src.persistence.history_store import HistoryStore

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("qr-payment-agent")

app = FastAPI(title="QR Payment Agent API", version="1.0.0")

# ---- CORS (React dev server + Render) ----
# Set FRONTEND_ORIGIN in Render: https://your-frontend-domain.com
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)

# ---- Request ID middleware ----
@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "request_id": request_id},
            headers={"X-Request-Id": request_id},
        )
    response.headers["X-Request-Id"] = request_id
    return response


# ---- Agent wiring ----
sessions = InMemorySessionService()
memory = SimpleMemoryBank()

# Default UI user profile (can be expanded later)
memory.upsert_profile("user-123", {
    "home_currency": "INR",
    "preferred_card": "VISA",
    "risk_preference": "balanced",
})

orchestrator = OrchestratorAgent(sessions, memory)

# ---- Persistent history ----
history_store = HistoryStore(db_path=os.getenv("HISTORY_DB_PATH", "data/history.db"))


# ----------------------------
# Helpers
# ----------------------------
def _extract_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize both single-QR and multi-QR output into:
    total_home, home_currency, risk_level, note/message
    """
    # Multi QR
    if result.get("multiple") is True:
        total_home = result.get("total_home", 0.0)
        msg = result.get("message") or result.get("message", "") or "Multi QR processed."
        # risk: mixed if not uniform
        risk_levels = []
        for item in result.get("items", []):
            r = (item.get("risk_result") or {}).get("risk_level")
            if r:
                risk_levels.append(r)
        risk_level = "mixed" if len(set(risk_levels)) > 1 else (risk_levels[0] if risk_levels else "unknown")
        return {
            "total_home": float(total_home) if isinstance(total_home, (int, float)) else 0.0,
            "home_currency": "INR",  # your app is INRs by profile; UI can show this
            "risk_level": risk_level,
            "note": msg,
        }

    # Single QR
    fx = result.get("fx_result") or {}
    risk = result.get("risk_result") or {}
    msg = result.get("message") or "Done."
    return {
        "total_home": float(fx.get("total_home", 0.0)) if isinstance(fx.get("total_home"), (int, float)) else 0.0,
        "home_currency": fx.get("to_currency", "INR"),
        "risk_level": risk.get("risk_level", "unknown"),
        "note": msg,
    }


# ----------------------------
# Schemas
# ----------------------------
class ScanTextRequest(BaseModel):
    user_id: str = "user-123"
    session_id: str = ""
    qr_payload: str


# ----------------------------
# Routes
# ----------------------------
@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/scan-text")
def scan_text(req: ScanTextRequest):
    """
    Body: { user_id, session_id, qr_payload }
    """
    user_id = req.user_id
    session_id = req.session_id or ""

    logger.info("scan_text user_id=%s session_id=%s", user_id, session_id)

    result = orchestrator.handle_qr_scan(
        user_id=user_id,
        session_id=session_id,
        qr_payload=req.qr_payload,
    )

    summary = _extract_summary(result)
    history_store.add(
        user_id=user_id,
        mode="text",
        input_repr=req.qr_payload[:2000],
        total_home=summary["total_home"],
        home_currency=summary["home_currency"],
        risk_level=summary["risk_level"],
        note=summary["note"],
        raw_result=result,
    )

    # IMPORTANT: include summary so UI doesn’t struggle
    return {"result": result, "summary": summary}


@app.post("/api/scan-image")
async def scan_image(
    file: UploadFile = File(...),
    user_id: str = Query("user-123"),
    session_id: str = Query(""),
):
    """
    multipart/form-data file upload
    """
    logger.info("scan_image user_id=%s session_id=%s filename=%s", user_id, session_id, file.filename)

    # Save upload to a real temp file (Windows/Render safe)
    suffix = os.path.splitext(file.filename or "qr.png")[1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        result = orchestrator.handle_qr_image_scan(
            user_id=user_id,
            session_id=session_id or "",
            image_path=tmp_path,
        )
    finally:
        # cleanup
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    summary = _extract_summary(result)
    history_store.add(
        user_id=user_id,
        mode="image",
        input_repr=file.filename or "uploaded-image",
        total_home=summary["total_home"],
        home_currency=summary["home_currency"],
        risk_level=summary["risk_level"],
        note=summary["note"],
        raw_result=result,
    )

    return {"result": result, "summary": summary}


@app.get("/api/history")
def history(user_id: str = "user-123", limit: int = 50):
    """
    Returns compact history rows for UI tables.
    """
    rows = history_store.list(user_id=user_id, limit=limit)
    return {"user_id": user_id, "items": rows}

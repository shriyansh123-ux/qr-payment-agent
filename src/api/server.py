"""API for a locally configured single-user demo.

X-API-Key is a shared development key, not end-user identity. Keep this API
on a trusted network; use an identity provider before internet-scale usage.
"""
import hmac
import os
import tempfile
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Query, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError
from src.agents.fx_rate_agent import FXUnavailable
from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank

app = FastAPI(title="QR Payment Agent API")
origins = [v.strip() for v in os.getenv("QR_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-API-Key"])
sessions = InMemorySessionService()
memory = SimpleMemoryBank()
orchestrator = OrchestratorAgent(sessions, memory)
MAX_UPLOAD_BYTES = 3 * 1024 * 1024


def auth(x_api_key: Optional[str] = Header(None)):
    configured = os.getenv("QR_API_KEY", "")
    if len(configured) < 24:
        raise HTTPException(status_code=503, detail="Server API key is not configured")
    if not x_api_key or not hmac.compare_digest(x_api_key, configured):
        raise HTTPException(status_code=401, detail="Invalid API key")


class ScanTextRequest(BaseModel):
    user_id: str = Field(default="demo-user", max_length=80)
    session_id: str = Field(default="", max_length=100)
    qr_payload: str = Field(min_length=1, max_length=8192)
    user_country: Optional[str] = Field(default=None, max_length=2)


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except FXUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok", "ok": True, "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/scan-text", dependencies=[Depends(auth)])
def scan_text(req: ScanTextRequest):
    result = _run(orchestrator.handle_qr_scan, "demo-user", req.session_id,
                  req.qr_payload, req.user_country)
    return {"success": True, **result}


@app.post("/api/scan-image", dependencies=[Depends(auth)])
async def scan_image(file: UploadFile = File(...), user_id: str = Query("demo-user"),
                     session_id: str = Query(""), user_country: Optional[str] = Query(None)):
    if file.content_type not in ("image/png", "image/jpeg", "image/webp"):
        raise HTTPException(415, detail="Only PNG, JPEG, and WebP images are supported")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail="Image must be 1 byte to 3 MiB")
    from io import BytesIO
    try:
        with Image.open(BytesIO(content)) as img:
            if img.format not in ("PNG", "JPEG", "WEBP") or img.width > 5000 or img.height > 5000 or img.width * img.height > 12_000_000:
                raise ValueError("Image format or dimensions not supported")
            img.verify()
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, detail="Invalid or oversized image") from exc
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        path = tmp.name
        tmp.write(content)
    try:
        return {"success": True, **_run(orchestrator.handle_qr_image_scan,
                "demo-user", session_id, path, user_country)}
    finally:
        os.unlink(path)


@app.get("/api/history", dependencies=[Depends(auth)])
def history(user_id: str = Query("demo-user"), session_id: str = Query("")):
    state = sessions.get_session(session_id) if session_id else None
    return {"user_id": "demo-user", "session_id": session_id,
            "items": list(state.history) if state else [], "history": list(state.history) if state else []}


@app.post("/api/clear-history", dependencies=[Depends(auth)])
def clear_history(user_id: str = Query("demo-user"), session_id: str = Query("")):
    state = sessions.get_session(session_id) if session_id else None
    if state:
        state.history = []
        sessions.update_session(state)
    return {"ok": True, "user_id": "demo-user", "session_id": session_id}


# Serve the production React build from the same HTTP origin when present.
# Local Python-only development still works without building React.
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
if (frontend_dist / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

# src/api/server.py

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
import os
import shutil
import traceback

from src.api.models import (
    TextScanRequest,
    HistoryResponse,
    HistoryItem,
)
from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank


# --- Setup global services ---

sessions = InMemorySessionService()
memory = SimpleMemoryBank()

# Seed a default profile for a known user (not strictly required now)
DEFAULT_USER_ID = "api-user"
memory.upsert_profile(DEFAULT_USER_ID, {
    "home_currency": "INR",
    "preferred_card": "VISA",
    "risk_preference": "balanced",
})

orchestrator = OrchestratorAgent(sessions, memory)

# Simple in-memory history for demo
api_history: List[HistoryItem] = []


def ensure_user_profile(user_id: str):
    """
    Ensure that the given user_id has a profile in the memory bank.
    If not, create a default one.
    """
    profile = memory.get_profile(user_id)
    if not profile:
        memory.upsert_profile(user_id, {
            "home_currency": "INR",
            "preferred_card": "VISA",
            "risk_preference": "balanced",
        })


app = FastAPI(title="QR Payment Translator API")

# CORS so frontend / tools can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in real prod, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/api/scan-text")
def scan_text(req: TextScanRequest):
    """
    Scan a text QR payload and return the orchestrator result.
    We return a simple JSON structure without strict response_model,
    to avoid Pydantic validation issues while we're debugging.
    """
    try:
        ensure_user_profile(req.user_id)

        result = orchestrator.handle_qr_scan(
            user_id=req.user_id,
            session_id=req.session_id or "",
            qr_payload=req.qr_payload,
        )

        item = HistoryItem(
            timestamp=datetime.utcnow().isoformat(),
            mode="text",
            input_repr=req.qr_payload,
            home_currency=result["fx_result"].get("to_currency", ""),
            total_home=result["fx_result"].get("total_home"),
            risk_level=result["risk_result"].get("risk_level", ""),
            note=result["message"][:120],
        )
        api_history.append(item)

        # Wrap result in a consistent envelope
        return {
            "success": True,
            "session_id": result.get("session_id"),
            "qr_info": result.get("qr_info"),
            "fx_result": result.get("fx_result"),
            "risk_result": result.get("risk_result"),
            "message": result.get("message"),
        }

    except Exception as e:
        # Print full traceback in server console for debugging
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            },
        )


@app.post("/api/scan-image")
async def scan_image(
    user_id: str,
    session_id: str = "",
    file: UploadFile = File(...),
):
    """
    Accepts an uploaded image file, saves it temporarily,
    passes path to orchestrator.handle_qr_image_scan.
    """
    temp_path = None
    try:
        ensure_user_profile(user_id)

        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = orchestrator.handle_qr_image_scan(
            user_id=user_id,
            session_id=session_id or "",
            image_path=temp_path,
        )

        item = HistoryItem(
            timestamp=datetime.utcnow().isoformat(),
            mode="image",
            input_repr=f"image({file.filename})",
            home_currency=result["fx_result"].get("to_currency", ""),
            total_home=result["fx_result"].get("total_home"),
            risk_level=result["risk_result"].get("risk_level", ""),
            note=result["message"][:120],
        )
        api_history.append(item)

        return {
            "success": True,
            "session_id": result.get("session_id"),
            "qr_info": result.get("qr_info"),
            "fx_result": result.get("fx_result"),
            "risk_result": result.get("risk_result"),
            "message": result.get("message"),
        }

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
            },
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/api/history")
def get_history():
    """
    Return history as a simple JSON structure.
    """
    return {
        "items": [item.dict() for item in api_history]
    }

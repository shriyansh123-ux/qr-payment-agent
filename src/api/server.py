"""FastAPI app: QR estimates, manual conversion, optional accounts and the React build."""
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from src.api import accounts
from src.api.converter import router as converter_router
from src.api.deps import check_api_key, estimator, public_demo_enabled, require_api_key, run_estimate
from src.api.limits import api_rate_limit
from src.api.security import security_headers
from src.parsers.qr_text import is_demo_payload

MAX_UPLOAD_BYTES = 3 * 1024 * 1024
MAX_IMAGE_SIDE = 5000
MAX_IMAGE_PIXELS = 12_000_000
ALLOWED_IMAGE_TYPES = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    accounts.close_pools()


app = FastAPI(title="Travel QR Cost Estimator API", lifespan=lifespan)
app.include_router(accounts.router)
app.include_router(converter_router)
app.middleware("http")(api_rate_limit)
app.middleware("http")(security_headers)
origins = [v.strip() for v in os.getenv(
    "QR_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if v.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type", "X-API-Key", "Authorization"])


class ScanTextRequest(BaseModel):
    qr_payload: str = Field(min_length=1, max_length=8192)
    home_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


@app.get("/api/health")
def health():
    return {"status": "ok", "ok": True, "time": datetime.now(UTC).isoformat()}


@app.get("/api/config")
def public_config():
    """Lets the UI know whether keyless demo payloads are accepted."""
    return {"public_demo": public_demo_enabled()}


@app.post("/api/scan-text")
async def scan_text(req: ScanTextRequest, x_api_key: str | None = Header(None)):
    if x_api_key or not (public_demo_enabled() and is_demo_payload(req.qr_payload)):
        check_api_key(x_api_key)
    result = await run_estimate(estimator.estimate_text, req.qr_payload, req.home_currency)
    return {"success": True, **result}


def _validate_image(content: bytes, content_type: str | None) -> None:
    expected_format = ALLOWED_IMAGE_TYPES.get(content_type or "")
    if expected_format is None:
        raise HTTPException(415, detail="Only PNG, JPEG, and WebP images are supported")
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail="Image must be 1 byte to 3 MiB")
    try:
        with Image.open(BytesIO(content)) as img:
            if (img.format not in ALLOWED_IMAGE_TYPES.values()
                    or img.width > MAX_IMAGE_SIDE or img.height > MAX_IMAGE_SIDE
                    or img.width * img.height > MAX_IMAGE_PIXELS):
                raise ValueError("Image format or dimensions not supported")
            img.verify()
    except (UnidentifiedImageError, ValueError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, detail="Invalid or oversized image") from exc


@app.post("/api/scan-image", dependencies=[Depends(require_api_key)])
async def scan_image(file: UploadFile = File(...),
                     home_currency: str | None = Query(None, pattern=r"^[A-Z]{3}$")):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    _validate_image(content, file.content_type)
    result = await run_estimate(estimator.estimate_image, content, home_currency)
    return {"success": True, **result}


# Serve the production React build from the same origin when present.
frontend_dist = Path(__file__).resolve().parents[2] / "web" / "dist"
if (frontend_dist / "index.html").is_file():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

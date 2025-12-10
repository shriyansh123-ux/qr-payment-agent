from pydantic import BaseModel
from typing import Optional, Any, List, Dict


class TextScanRequest(BaseModel):
    user_id: str
    qr_payload: str
    session_id: Optional[str] = ""


class ImageScanRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = ""
    # We will accept files via FastAPI UploadFile instead of here


class ScanResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    qr_info: Dict[str, Any]
    fx_result: Dict[str, Any]
    risk_result: Dict[str, Any]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str


class HistoryItem(BaseModel):
    timestamp: str
    mode: str
    input_repr: str
    home_currency: str
    total_home: Optional[float]
    risk_level: str
    note: str


class HistoryResponse(BaseModel):
    items: List[HistoryItem]

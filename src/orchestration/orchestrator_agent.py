"""QR parsing and dated reference conversion, without risk scoring or AI calls."""
from decimal import Decimal
from typing import Optional

from src.agents.qr_image_agent import QRImageAgent
from src.agents.qr_parser_agent import QRParserAgent
from src.agents.fx_rate_agent import FXRateAgent
from src.orchestration.session_manager import InMemorySessionService, compact_history
from src.orchestration.memory_manager import SimpleMemoryBank
from src.config import HOME_CURRENCY


class OrchestratorAgent:
    def __init__(self, session_service: InMemorySessionService, memory_bank: SimpleMemoryBank):
        self.sessions = session_service
        self.memory = memory_bank
        self.qr_agent = QRParserAgent()
        self.fx_agent = FXRateAgent()
        self.qr_image_agent = QRImageAgent()

    def _get_or_create_session(self, session_id):
        if not session_id:
            return self.sessions.create_session()
        existing = self.sessions.get_session(session_id)
        return existing if existing is not None else self.sessions.create_session()

    def handle_qr_scan(self, user_id: str, session_id: str, qr_payload: str,
                       user_country: Optional[str] = None):
        # user_country is accepted only for compatibility; it is not used as location evidence.
        payload = (qr_payload or "").strip()
        if not payload:
            raise ValueError("Please provide a QR payload.")
        parsed = self.qr_agent.handle(payload)
        if not isinstance(parsed, dict):
            raise ValueError("QR parser returned an invalid format.")
        multiple = parsed.get("multiple") is True
        items = parsed.get("items", []) if multiple else [parsed]
        if not items:
            raise ValueError("No valid QR items found.")
        home = (self.memory.get_profile(user_id) or {}).get("home_currency", HOME_CURRENCY)
        results = [{"qr_info": item, "fx_result": self.fx_agent.handle(
            amount_local=item["amount"], local_currency=item["currency"], home_currency=home
        )} for item in items]
        total = sum((Decimal(str(item["fx_result"]["total_home"])) for item in results), Decimal(0))
        message = f"Reference conversion before provider fees: {total:.2f} {home}. This app does not make payments."
        state = self._get_or_create_session(session_id)
        state.history = compact_history(state.history)
        state.history.extend([
            {"role": "user", "content": "User scanned payment QR content."},
            {"role": "assistant", "content": message},
        ])
        self.sessions.update_session(state)
        if multiple:
            return {"session_id": state.session_id, "multiple": True, "count": len(results),
                    "items": results, "total_home": float(total), "message": message}
        return {"session_id": state.session_id, **results[0], "message": message}

    def handle_qr_image_scan(self, user_id: str, session_id: str, image_path: str,
                            user_country: Optional[str] = None):
        payload = self.qr_image_agent.handle(image_path)
        if isinstance(payload, (list, tuple)):
            payload = ",".join(str(item).strip() for item in payload if str(item).strip())
        payload = str(payload or "").strip()
        if payload.startswith("[") and payload.endswith("]"):
            payload = payload[1:-1].strip().strip("'").strip('"')
        return self.handle_qr_scan(user_id, session_id, payload, user_country)

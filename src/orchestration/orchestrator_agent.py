import logging

from src.agents.qr_image_agent import QRImageAgent
from src.agents.qr_parser_agent import QRParserAgent
from src.agents.fx_rate_agent import FXRateAgent
from src.agents.risk_guard_agent import RiskGuardAgent
from src.orchestration.session_manager import (
    InMemorySessionService,
    compact_history,
)
from src.orchestration.memory_manager import SimpleMemoryBank
from src.tools.gemini_http_client import call_gemini, GeminiHTTPError
from src.config import HOME_CURRENCY

logger = logging.getLogger(__name__)


class OrchestratorAgent(object):
    def __init__(self, session_service: InMemorySessionService, memory_bank: SimpleMemoryBank):
        self.sessions = session_service
        self.memory = memory_bank
        self.qr_agent = QRParserAgent()
        self.fx_agent = FXRateAgent()
        self.risk_agent = RiskGuardAgent()
        self.qr_image_agent = QRImageAgent()  # image-based QR decoder

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self, user_profile: dict) -> str:
        home_currency = user_profile.get("home_currency", HOME_CURRENCY)
        risk_pref = user_profile.get("risk_preference", "balanced")
        return (
            "You are a travel payment assistant agent. "
            f"The user's home currency is {home_currency}. "
            f"User risk preference: {risk_pref}. "
            "Always explain final amounts in home currency and give a clear, concise risk note."
        )

    # ------------------------------------------------------------------
    # Core single-QR flow (used for both text and per-QR image decoding)
    # ------------------------------------------------------------------

    def handle_qr_scan(self, user_id: str, session_id: str, qr_payload: str) -> dict:
        """
        Handle a single QR payload string.

        Returns a dict with:
        - session_id
        - qr_info
        - fx_result
        - risk_result
        - message (LLM or fallback)
        """
        # 1. Get or create session
        if not session_id:
            state = self.sessions.create_session()
        else:
            existing = self.sessions.get_session(session_id)
            state = existing if existing is not None else self.sessions.create_session()

        # 2. Load user profile
        profile = self.memory.get_profile(user_id)
        system_prompt = self._build_system_prompt(profile)

        # 3. Decode QR
        qr_info = self.qr_agent.handle(qr_payload)

        # MULTI-QR CASE
        if isinstance(qr_info, dict) and qr_info.get("multiple"):
            results = []
        for item in qr_info["items"]:
            r = self.handle_qr_scan(
            user_id=user_id,
            session_id=session_id,
            qr_payload=item["raw"]
        )
        results.append(r)

        return {
        "multiple": True,
        "count": len(results),
        "results": results
        }

        logger.info("Decoded QR: %s", qr_info)

        # 4. Compute FX and risk
        fx_result = self.fx_agent.handle(
            amount_local=qr_info["amount"],
            local_currency=qr_info["currency"],
            home_currency=profile.get("home_currency", HOME_CURRENCY),
        )
        logger.info("FX result: %s", fx_result)

        risk_result = self.risk_agent.handle(
            merchant_id=qr_info["merchant_id"],
            country=qr_info["country"],
            amount=qr_info["amount"],
        )
        logger.info("Risk result: %s", risk_result)

        # 5. Prepare conversation + prompt
        state.history = compact_history(state.history)
        state.history.append({"role": "user", "content": f"User scanned QR: {qr_payload}"})

        tool_summary = (
            f"Decoded QR: {qr_info}\n"
            f"FX result: {fx_result}\n"
            f"Risk result: {risk_result}\n"
        )

        convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.history)

        prompt = (
            system_prompt
            + "\n\nConversation so far:\n"
            + convo_text
            + "\n\n---\n"
            + "Tool results:\n" + tool_summary
            + "\n\nNow respond to the user. "
              "Include: final cost in home currency, short fee breakdown, and a risk recommendation."
        )

        # 6. Call Gemini (HTTP), with safe fallback
        try:
            response_text = call_gemini(prompt)
        except GeminiHTTPError as e:
            logger.error("Gemini HTTP call failed: %s", e)
            total = fx_result["total_home"]
            home_cur = fx_result["to_currency"]
            base = fx_result["base_home"]
            markup = fx_result["markup_home"]
            fee = fx_result["network_fee_home"]
            risk = risk_result["risk_level"]

            response_text = (
                "I could not reach the language model service right now, "
                "but here is a computed breakdown:\n"
                f"- Base converted amount: {base:.2f} {home_cur}\n"
                f"- FX markup: {markup:.2f} {home_cur}\n"
                f"- Network fee (approx.): {fee:.2f} {home_cur}\n"
                f"- Total estimated charge: {total:.2f} {home_cur}\n"
                f"- Risk level: {risk}\n"
                "Recommendation: Proceed only if this total and risk level match your expectation."
            )

        state.history.append({"role": "assistant", "content": response_text})
        self.sessions.update_session(state)

        # VERY IMPORTANT: RETURN a dict
        return {
            "session_id": state.session_id,
            "qr_info": qr_info,
            "fx_result": fx_result,
            "risk_result": risk_result,
            "message": response_text,
        }

    # ------------------------------------------------------------------
    # New: image-based multi-QR flow
    # ------------------------------------------------------------------

    def handle_qr_image_scan(self, user_id: str, session_id: str, image_path: str) -> dict:
        """
        Scan one or multiple QR codes from an image.

        - If 0 QRs: raises ValueError.
        - If 1 QR: returns the same structure as handle_qr_scan (single dict).
        - If >1 QRs: returns a dict:
            {
              "multiple": True,
              "count": N,
              "results": [ <single-QR dict>, ... ],
              "message": "Decoded N QR codes from this image. See JSON for full breakdown."
            }
        """
        qr_payloads = self.qr_image_agent.handle(image_path)

        # Normalize to list
        if isinstance(qr_payloads, str):
            qr_payloads = [qr_payloads]

        if not qr_payloads:
            raise ValueError("No QR codes found in the image.")

        # Single QR: reuse existing flow
        if len(qr_payloads) == 1:
            return self.handle_qr_scan(
                user_id=user_id,
                session_id=session_id,
                qr_payload=qr_payloads[0],
            )

        # Multi-QR: process each one independently
        results = []
        for payload in qr_payloads:
            # For simplicity, let each call manage its own session (session_id="").
            res = self.handle_qr_scan(
                user_id=user_id,
                session_id="",
                qr_payload=payload,
            )
            results.append(res)

        return {
            "multiple": True,
            "count": len(results),
            "results": results,
            "message": f"Decoded {len(results)} QR codes from this image. See JSON for full breakdown.",
        }

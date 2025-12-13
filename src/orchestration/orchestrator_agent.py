import logging
from typing import Dict, Any, List

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
        self.risk_agent = RiskGuardAgent(memory_bank)
        self.qr_image_agent = QRImageAgent()

    # -------------------------
    # Prompt building
    # -------------------------
    def _build_system_prompt(self, user_profile: dict) -> str:
        home_currency = user_profile.get("home_currency", HOME_CURRENCY)
        risk_pref = user_profile.get("risk_preference", "balanced")
        return (
            "You are a travel payment assistant agent. "
            f"The user's home currency is {home_currency}. "
            f"User risk preference: {risk_pref}. "
            "Always explain final amounts in home currency and give a clear, concise risk note."
        )

    # -------------------------
    # Helpers
    # -------------------------
    def _get_or_create_session(self, session_id: str):
        if not session_id:
            return self.sessions.create_session()

        existing = self.sessions.get_session(session_id)
        return existing if existing is not None else self.sessions.create_session()

    def _fallback_message(self, fx_result: dict, risk_result: dict) -> str:
        total = fx_result.get("total_home", 0.0)
        home_cur = fx_result.get("to_currency", HOME_CURRENCY)
        base = fx_result.get("base_home", 0.0)
        markup = fx_result.get("markup_home", 0.0)
        fee = fx_result.get("network_fee_home", 0.0)
        risk = risk_result.get("risk_level", "unknown")

        return (
            "I could not reach the language model service right now, "
            "but here is a computed breakdown:\n"
            f"- Base converted amount: {base:.2f} {home_cur}\n"
            f"- FX markup: {markup:.2f} {home_cur}\n"
            f"- Network fee (approx.): {fee:.2f} {home_cur}\n"
            f"- Total estimated charge: {total:.2f} {home_cur}\n"
            f"- Risk level: {risk}\n"
            "Recommendation: Proceed only if this total and risk level match your expectation."
        )

    # -------------------------
    # Main: TEXT QR scan
    # -------------------------
    def handle_qr_scan(self, user_id: str, session_id: str, qr_payload: str) -> Dict[str, Any]:
        # 1) session + profile
        state = self._get_or_create_session(session_id)
        user_profile = self.memory.get_profile(user_id) or {}
        home_currency = user_profile.get("home_currency", HOME_CURRENCY)
        system_prompt = self._build_system_prompt(user_profile)

        # 2) Parse QR
        qr_info = self.qr_agent.handle(qr_payload)

        # ---------- MULTI-QR ----------
        if isinstance(qr_info, dict) and qr_info.get("multiple") is True:
            items: List[Dict[str, Any]] = qr_info.get("items", [])
            if not items:
                return {
                    "session_id": state.session_id,
                    "multiple": True,
                    "count": 0,
                    "items": [],
                    "total_home": 0.0,
                    "message": "No valid QR items found in the provided input.",
                }

            results = []
            total_home_sum = 0.0

            for item in items:
                fx = self.fx_agent.handle(
                    amount_local=item["amount"],
                    local_currency=item["currency"],
                    home_currency=home_currency,
                )
                risk = self.risk_agent.handle(
                    merchant_id=item["merchant_id"],
                    country=item["country"],
                    amount=item["amount"],
                )

                # update memory
                self.memory.add_recent_merchant(item["merchant_id"], item["country"])

                total_home_sum += float(fx.get("total_home", 0.0))

                results.append({
                    "qr_info": item,
                    "fx_result": fx,
                    "risk_result": risk,
                })

            # session history
            state.history = compact_history(state.history)
            state.history.append({"role": "user", "content": f"User scanned MULTI QR: {qr_payload}"})

            tool_summary = f"Multi-QR results: {results}\nTotal home sum: {total_home_sum}\n"
            convo_text = "\n".join(f"{m['role']}: {m['content']}" for m in state.history)

            prompt = (
                system_prompt
                + "\n\nConversation so far:\n"
                + convo_text
                + "\n\n---\nTool results:\n"
                + tool_summary
                + "\n\nNow respond to the user with: "
                  "a short summary, total cost in home currency, and any high-risk warning if present."
            )

            try:
                response_text = call_gemini(prompt)
            except GeminiHTTPError as e:
                logger.error("Gemini HTTP call failed (multi): %s", e)
                response_text = (
                    f"You scanned **{len(results)}** QR payments.\n\n"
                    f"**Total estimated charge: {total_home_sum:.2f} {home_currency}**\n"
                    "Open the JSON details to see per-QR breakdowns."
                )

            state.history.append({"role": "assistant", "content": response_text})
            self.sessions.update_session(state)

            return {
                "session_id": state.session_id,
                "multiple": True,
                "count": len(results),
                "items": results,
                "total_home": total_home_sum,
                "message": response_text,
            }

        # ---------- SINGLE-QR ----------
        if not isinstance(qr_info, dict):
            raise ValueError("QR parser returned invalid format (expected dict).")

        logger.info("Decoded QR: %s", qr_info)

        fx_result = self.fx_agent.handle(
            amount_local=qr_info["amount"],
            local_currency=qr_info["currency"],
            home_currency=home_currency,
        )
        logger.info("FX result: %s", fx_result)

        risk_result = self.risk_agent.handle(
            merchant_id=qr_info["merchant_id"],
            country=qr_info["country"],
            amount=qr_info["amount"],
        )

        self.memory.add_recent_merchant(qr_info["merchant_id"], qr_info["country"])
        logger.info("Risk result: %s", risk_result)

        # session history
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

        try:
            response_text = call_gemini(prompt)
        except GeminiHTTPError as e:
            logger.error("Gemini HTTP call failed: %s", e)
            response_text = self._fallback_message(fx_result, risk_result)

        state.history.append({"role": "assistant", "content": response_text})
        self.sessions.update_session(state)

        return {
            "session_id": state.session_id,
            "qr_info": qr_info,
            "fx_result": fx_result,
            "risk_result": risk_result,
            "message": response_text,
        }

    # -------------------------
    # Image QR scan
    # -------------------------
    def handle_qr_image_scan(self, user_id: str, session_id: str, image_path: str) -> Dict[str, Any]:
        """
        1) Decode QR payload from image
        2) Normalize it (list/['..']/None cases)
        3) Reuse handle_qr_scan for full flow
        """
        qr_payload = self.qr_image_agent.handle(image_path)

        # if list/tuple -> join
        if isinstance(qr_payload, (list, tuple)):
            qr_payload = ",".join([str(x).strip() for x in qr_payload if str(x).strip()])

        if qr_payload is None:
            qr_payload = ""

        qr_payload = str(qr_payload).strip()

        # Clean accidental python-list-string formatting like "['QR:JP:JPY:1500']"
        if qr_payload.startswith("[") and qr_payload.endswith("]"):
            qr_payload = qr_payload.strip("[]").strip()
            qr_payload = qr_payload.strip("'\"").strip()

        return self.handle_qr_scan(
            user_id=user_id,
            session_id=session_id,
            qr_payload=qr_payload,
        )

from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank
from src.observability.logging_config import setup_logging


def main():
    setup_logging()

    sessions = InMemorySessionService()
    memory = SimpleMemoryBank()

    # Seed user profile
    user_id = "user-123"
    memory.upsert_profile(user_id, {
        "home_currency": "INR",
        "preferred_card": "VISA_CREDIT",
        "risk_preference": "balanced",
    })

    orchestrator = OrchestratorAgent(sessions, memory)

    print("=== Universal Global QR Payment Translator Agent ===")
    mode = input("Do you want to scan a text QR or an image QR? (t/i): ").strip().lower()

    if mode == "i":
        # Image mode
        image_path = input("Enter the full path to the QR image file: ").strip()
        result = orchestrator.handle_qr_image_scan(
            user_id=user_id,
            session_id="",
            image_path=image_path
        )
    else:
        # Text mode (default if user types anything else)
        qr_payload = input("Paste QR payload (e.g., QR:JP:JPY:1500): ").strip()
        result = orchestrator.handle_qr_scan(
            user_id=user_id,
            session_id="",
            qr_payload=qr_payload
        )

    print("\n=== Agent Response ===")
    print(result["message"])
    print("\nRaw details:\n", result)


if __name__ == "__main__":
    main()

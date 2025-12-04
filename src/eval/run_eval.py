import json
from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank
from src.observability.logging_config import setup_logging

# Test QR payloads for evaluation
test_qrs = [
    "QR:JP:JPY:1500",
    "QR:US:USD:12",
    "QR:TH:THB:400",
    "QR:EU:EUR:9.5"
]

def run_eval():
    setup_logging()

    # Create session + memory objects
    sessions = InMemorySessionService()
    memory = SimpleMemoryBank()

    # Define a user profile for evaluation purposes
    user_id = "eval-user"
    memory.upsert_profile(user_id, {"home_currency": "INR", "risk_preference": "balanced"})

    # Orchestrator agent controls all sub-agents
    orchestrator = OrchestratorAgent(sessions, memory)

    results = []

    # Run evaluation for each QR payload
    for qr in test_qrs:
        out = orchestrator.handle_qr_scan(user_id, "", qr)
        results.append({
            "input_qr": qr,
            "agent_output": out["message"]
        })

    # Print results in readable JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run_eval()

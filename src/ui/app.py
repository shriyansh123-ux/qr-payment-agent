import time
import gradio as gr
import os
from datetime import datetime

from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank

try:
    import pandas as pd  # optional, for type checking history
except ImportError:
    pd = None


def _normalize_history(current_history):
    """
    Gradio sometimes passes a list (good) and sometimes a pandas.DataFrame.
    Convert everything to a plain list-of-rows.
    """
    if current_history is None:
        return []

    # DataFrame case
    if hasattr(current_history, "values"):
        # values -> numpy array -> list of rows
        return current_history.values.tolist()

    return current_history


# ---------- Agent wiring (same backend as CLI) ----------

sessions = InMemorySessionService()
memory = SimpleMemoryBank()

user_id = "ui-user"
memory.upsert_profile(user_id, {
    "home_currency": "INR",
    "preferred_card": "VISA",
    "risk_preference": "balanced",
})

orchestrator = OrchestratorAgent(sessions, memory)

# UI history: list of rows
history_store = []


def summarize_result(result, mode: str, input_repr: str):
    """
    Create a single row (list of 7 values) for the history table:
    [time, mode, input, home_currency, total_home, risk, note]
    """
    ts = datetime.now().strftime("%H:%M:%S")

    # Multi-QR case – reserved for future multi-QR support
    if isinstance(result, dict) and result.get("multiple"):
        return [
            ts,
            mode,
            f"{input_repr} (multi: {result.get('count', 0)} QRs)",
            "",
            "",
            "",
            "Multiple QR codes decoded",
        ]

    # Single QR case
    fx = result.get("fx_result", {}) if isinstance(result, dict) else {}
    risk = result.get("risk_result", {}) if isinstance(result, dict) else {}
    home_cur = fx.get("to_currency", "")
    total = fx.get("total_home", "")
    risk_level = risk.get("risk_level", "")
    msg = result.get("message", "") if isinstance(result, dict) else str(result)
    if len(msg) > 80:
        msg = msg[:77] + "..."

    total_str = f"{total:.2f}" if isinstance(total, (int, float)) else ""

    return [
        ts,
        mode,
        input_repr,
        home_cur,
        total_str,
        risk_level,
        msg,
    ]


def set_status_loading():
    return "⏳ Translating payment... please wait."


def set_status_done():
    return "✅ Translation complete."


def extract_message(json_result):
    """
    Turn the agent JSON into a human-readable explanation for the UI.
    """
    if isinstance(json_result, dict):
        if "message" in json_result and json_result["message"]:
            return json_result["message"]
        if "error" in json_result and json_result["error"]:
            return f"⚠️ {json_result['error']}"
        # fallback pretty-print
        return "No natural-language message available. See JSON on the right."
    else:
        return str(json_result)


def process_request(input_mode, image, qr_text, current_history):
    """
    Main UI handler.
    - input_mode: "Image" or "Text"
    - image: uploaded image file path (or None)
    - qr_text: string payload (or "")
    - current_history: previous history rows (list or DataFrame)
    """
    global history_store

    # Make sure we always work with a Python list-of-rows
    history_list = _normalize_history(current_history)

    try:
        # ----- 1. Run the agent -----
        if input_mode == "Image":
            if image is None:
                return {"error": "Please upload a QR image."}, history_list

            # In your Gradio version (type='filepath'), `image` is a string path
            if isinstance(image, str):
                path = image
            else:
                # fallback, just in case
                path = getattr(image, "name", str(image))

            result = orchestrator.handle_qr_image_scan(
                user_id=user_id,
                session_id="",
                image_path=path,
            )
            filename = os.path.basename(path)
            input_repr = f"image({filename})"

        else:  # Text mode
            qr_text = (qr_text or "").strip()
            if not qr_text:
                return {"error": "Please enter a QR payload string."}, history_list

            result = orchestrator.handle_qr_scan(
                user_id=user_id,
                session_id="",
                qr_payload=qr_text,
            )
            input_repr = qr_text

        # small artificial delay so spinner / status is visible
        time.sleep(0.5)

        # ----- 2. Normalize result for JSON widget -----
        if isinstance(result, (dict, list)):
            json_result = result
        else:
            json_result = {"result": str(result)}

        # ----- 3. Update history table -----
        row = summarize_result(json_result, input_mode, input_repr)
        history_list = history_list + [row]
        history_store = history_list

        return json_result, history_list

    except Exception as e:
        # Catch any unexpected error and format safely for JSON widget
        err_msg = f"Error while processing: {e}"

        row = [
            datetime.now().strftime("%H:%M:%S"),
            input_mode,
            "ERROR",
            "",
            "",
            "",
            err_msg,
        ]
        history_list = history_list + [row]
        history_store = history_list

        return {"error": err_msg}, history_list


def clear_history():
    """
    Clear the UI history table.
    """
    global history_store
    history_store = []
    return [], []


# ---------- Custom CSS for dark mode & nicer layout ----------

custom_css = """
body { background-color: #020617; }
.gradio-container { background-color: #020617 !important; color: #e5e7eb !important; }
.gr-button { border-radius: 9999px !important; padding: 0.6rem 1.4rem !important; }
#title { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
#subtitle { opacity: 0.8; }
"""


# ---------- Build Gradio UI (image + text, preview, history) ----------

with gr.Blocks() as demo:
    # Inject CSS manually (compatible with older Gradio)
    gr.HTML(f"<style>{custom_css}</style>")

    gr.Markdown(
        "<div id='title'>Universal QR Payment Translator</div>"
        "<div id='subtitle'>Upload a QR image or paste a QR string. "
        "Get FX, fees and risk in your home currency.</div>"
    )

    with gr.Row():
        input_mode = gr.Radio(
            ["Image", "Text"],
            value="Image",
            label="Input Type",
        )

    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(
                type="filepath",
                label="QR Image (drag & drop / paste)",
                sources=["upload", "clipboard", "drag"],  # paste & drag support
            )
            qr_text_input = gr.Textbox(
                lines=2,
                label="QR Text (e.g., QR:JP:JPY:1500)",
                placeholder="Paste QR payload here...",
            )
        with gr.Column(scale=1):
            output_json = gr.JSON(
                label="Agent Response (JSON)",
            )
            friendly_md = gr.Markdown(
                label="Human explanation",
            )

    run_button = gr.Button("Translate Payment", variant="primary")
    status_md = gr.Markdown("")  # status line under the button
    history_state = gr.State([])

    gr.Markdown("### History")
    with gr.Row():
        clear_button = gr.Button("Clear History", variant="secondary")
    history_table = gr.Dataframe(
        headers=["time", "mode", "input", "home_currency", "total_home", "risk", "note"],
        label="Previous Requests",
        interactive=False,
        wrap=True,
    )

    # Clear history button
    clear_button.click(
        fn=clear_history,
        inputs=None,
        outputs=[history_table, history_state],
    )

    # When button is clicked: set status -> run agent -> show message -> set status done -> sync state
    run_button.click(
        fn=set_status_loading,
        inputs=None,
        outputs=status_md,
    ).then(
        fn=process_request,
        inputs=[input_mode, image_input, qr_text_input, history_state],
        outputs=[output_json, history_table],
        api_name="translate",
        show_progress=True,  # shows animated spinner
    ).then(
        fn=extract_message,
        inputs=output_json,
        outputs=friendly_md,
    ).then(
        fn=set_status_done,
        inputs=None,
        outputs=status_md,
    ).then(
        fn=lambda h: h,
        inputs=history_table,
        outputs=history_state,
    )


if __name__ == "__main__":
    import os
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860"))
    )

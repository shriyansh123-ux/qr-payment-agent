import os
import time
from datetime import datetime
import gradio as gr

from src.orchestration.orchestrator_agent import OrchestratorAgent
from src.orchestration.session_manager import InMemorySessionService
from src.orchestration.memory_manager import SimpleMemoryBank
from src.observability.logging_config import setup_logging


setup_logging()

# ---- Backend wiring ----
sessions = InMemorySessionService()
memory = SimpleMemoryBank()

user_id = "ui-user"
memory.upsert_profile(user_id, {
    "home_currency": "INR",
    "preferred_card": "VISA",
    "risk_preference": "balanced",
})

orchestrator = OrchestratorAgent(sessions, memory)


def _as_list(history):
    """
    Gradio Dataframe sometimes passes list, sometimes DataFrame-like.
    Normalize to list-of-rows.
    """
    if history is None:
        return []
    if hasattr(history, "values"):
        return history.values.tolist()
    return history


def summarize_row(result: dict, mode: str, input_repr: str):
    ts = datetime.now().strftime("%H:%M:%S")

    if result.get("multiple"):
        total = result.get("total_home", 0.0)
        msg = result.get("message", "")
        return [ts, mode, input_repr, "INR", f"{total:.2f}", "mixed", msg[:120]]

    fx = result.get("fx_result", {})
    risk = result.get("risk_result", {})
    home_cur = fx.get("to_currency", "INR")
    total = fx.get("total_home", 0.0)
    risk_level = risk.get("risk_level", "")
    msg = result.get("message", "")

    return [ts, mode, input_repr, home_cur, f"{float(total):.2f}", risk_level, msg[:120]]


def process_request(input_mode, image, qr_text, history):
    history_list = _as_list(history)

    try:
        if input_mode == "Image":
            if not image:
                return {"error": "Please upload a QR image."}, history_list

            # In many Gradio versions, type="filepath" gives a string path
            if isinstance(image, str):
                path = image
            else:
                path = getattr(image, "name", None) or str(image)

            result = orchestrator.handle_qr_image_scan(
                user_id=user_id,
                session_id="",
                image_path=path,
            )

            input_repr = f"image({os.path.basename(path)})"

        else:
            qr_text = (qr_text or "").strip()
            if not qr_text:
                return {"error": "Please enter a QR payload string."}, history_list

            result = orchestrator.handle_qr_scan(
                user_id=user_id,
                session_id="",
                qr_payload=qr_text,
            )

            input_repr = qr_text

        time.sleep(0.2)
        row = summarize_row(result, input_mode, input_repr)
        history_list = history_list + [row]

        return result, history_list

    except Exception as e:
        err = {"error": f"{e}"}
        row = [datetime.now().strftime("%H:%M:%S"), input_mode, "ERROR", "", "", "", str(e)[:120]]
        history_list = history_list + [row]
        return err, history_list


custom_css = """
:root, body { background: #0b1220 !important; color: #e5e7eb !important; }
.gradio-container { background: #0b1220 !important; }
h1, h2, h3, label, p, span, div { color: #e5e7eb !important; }
table { background: #111827 !important; color: #e5e7eb !important; }
thead th { background: #0f172a !important; color: #e5e7eb !important; }
tbody td { color: #e5e7eb !important; }
.gr-button { border-radius: 9999px !important; padding: 0.6rem 1.2rem !important; }
"""


with gr.Blocks() as demo:
    gr.HTML(f"<style>{custom_css}</style>")

    gr.Markdown("# Universal QR Payment Translator")
    gr.Markdown("Upload a QR image or paste QR text (supports multi-QR separated by comma/newline).")

    input_mode = gr.Radio(["Image", "Text"], value="Image", label="Input Type")

    with gr.Row():
        image_input = gr.Image(type="filepath", label="QR Image (Upload/Drag)")
        qr_text_input = gr.Textbox(lines=2, label="QR Text", placeholder="QR:JP:JPY:1500,QR:US:USD:12")

    run_button = gr.Button("Translate Payment", variant="primary")

    output_json = gr.JSON(label="Agent Output")

    gr.Markdown("### History")
    history_table = gr.Dataframe(
        headers=["time", "mode", "input", "home_currency", "total_home", "risk", "note"],
        interactive=False,
        wrap=True,
    )

    state = gr.State([])

    run_button.click(
        fn=process_request,
        inputs=[input_mode, image_input, qr_text_input, state],
        outputs=[output_json, history_table],
        show_progress=True,
    ).then(
        fn=lambda h: h,
        inputs=history_table,
        outputs=state,
    )


if __name__ == "__main__":
    demo.launch()

"""Optional local Gradio interface. It calls the estimator directly with no
authentication, so keep it on your own machine: python -m src.ui.gradio_app
"""
from datetime import datetime
from pathlib import Path

import gradio as gr

from src.config import setup_logging
from src.services.estimator import CostEstimator

setup_logging()
estimator = CostEstimator()

CSS = """
:root, body, .gradio-container { background: #0b1220 !important; color: #e5e7eb !important; }
h1, h2, h3, label, p, span, div { color: #e5e7eb !important; }
table { background: #111827 !important; color: #e5e7eb !important; }
thead th { background: #0f172a !important; }
"""


def _rows(history):
    if history is None:
        return []
    return history.values.tolist() if hasattr(history, "values") else list(history)


def _summary(result: dict, mode: str, label: str) -> list:
    if result.get("multiple"):
        currency, total = result["home_currency"], result["total_home"]
    else:
        currency, total = result["fx_result"]["to_currency"], result["fx_result"]["total_home"]
    return [datetime.now().strftime("%H:%M:%S"), mode, label, currency, str(total), result["message"][:120]]


def process(mode, image_path, qr_text, history):
    rows = _rows(history)
    try:
        if mode == "Image":
            if not image_path:
                return "Please upload a QR image.", rows
            path = Path(image_path if isinstance(image_path, str) else image_path.name)
            result = estimator.estimate_image(path.read_bytes())
            label = f"image({path.name})"
        else:
            qr_text = (qr_text or "").strip()
            if not qr_text:
                return "Please enter a QR payload string.", rows
            result = estimator.estimate_text(qr_text)
            label = qr_text
        return result["message"], [*rows, _summary(result, mode, label)]
    except Exception as exc:  # shown to the local user, never logged remotely
        error_row = [datetime.now().strftime("%H:%M:%S"), mode, "ERROR", "", "", str(exc)[:120]]
        return str(exc), [*rows, error_row]


with gr.Blocks() as demo:
    gr.HTML(f"<style>{CSS}</style>")
    gr.Markdown("# Travel QR Cost Estimator")
    gr.Markdown("Upload a QR image or paste QR text (multiple QRs separated by comma/newline).")
    input_mode = gr.Radio(["Image", "Text"], value="Image", label="Input Type")
    with gr.Row():
        image_input = gr.Image(type="filepath", label="QR Image")
        qr_text_input = gr.Textbox(lines=2, label="QR Text", placeholder="QR:JP:JPY:1500,QR:US:USD:12")
    run_button = gr.Button("Estimate cost", variant="primary")
    output_summary = gr.Textbox(label="Conversion summary", lines=4)
    gr.Markdown("### History")
    history_table = gr.Dataframe(headers=["time", "mode", "input", "currency", "total", "note"],
                                 interactive=False, wrap=True)
    state = gr.State([])
    run_button.click(fn=process, inputs=[input_mode, image_input, qr_text_input, state],
                     outputs=[output_summary, history_table], show_progress=True
                     ).then(fn=lambda h: h, inputs=history_table, outputs=state)


if __name__ == "__main__":
    demo.launch()

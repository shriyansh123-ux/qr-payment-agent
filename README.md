Universal Global QR Payment Translator

A Multi-Agent AI System for Real-Time FX Conversion, Risk Scoring & QR Payment Interpretation

 1. Problem Statement

When travelling internationally, consumers frequently scan foreign QR codes for payments. But they face several issues:

No visibility of actual cost in home currency

Hidden FX markups and network fees

No fraud/risk guidance

Different QR formats across countries

No unified tool supporting both QR images and QR text payloads

 This leads to overpayment, confusion, and security risk.

 2. Solution Overview

The Universal Global QR Payment Translator solves this with a multi-agent AI system that:

 Parses QR codes

From text: QR:JP:JPY:1500

From images (drag & drop, upload, clipboard)

Supports multiple QRs in one string (multi-QR parsing)

 Computes FX conversion

Uses live FX API (open.er-api.com)

Automatic fallback to mock FX rates when offline

Includes markup, network fee, conversion breakdown

 Performs Intelligent Risk Scoring

A multi-signal reasoning engine evaluates:

Signal	Logic
Country familiarity	Distance risk scoring
Transaction size	Large / unusual payments
Merchant history	First-time merchant → higher risk
Bad merchant list	Suspicious merchants flagged
User preference	Balanced / conservative / risky
Currency patterns	Deviations from normal behavior

Generates: risk level + score + reasons

 Uses an LLM (Gemini) for explanations

The explanation agent produces natural-language guidance like:

“This transaction appears low risk. Your final cost will be ₹860.75 after FX markup and fees.”

 Provides a clean interactive UI (Gradio)

Text input

Image upload (filepath)

Multi-QR output

JSON inspector

History table

Dark mode

Status indicators

 Fully deployable as a cloud web app

Supports Render / Railway / Cloud Run.

 3. System Architecture
+---------------------------+
|       User Interface      | (Gradio UI)
| - Image Upload            |
| - Text Input              |
| - History Panel           |
+-------------+-------------+
              |
              v
+-------------+-------------------------------+
|               Orchestrator Agent            |
|  (Manages flow, session, memory, LLM calls) |
+-------------+-------------------------------+
      |                 |                |
      v                 v                v
+-----------+    +-------------+   +----------------+
| QR Agent  |    | FX Agent    |   | Risk Agent     |
| (text &   |    | - Live FX   |   | - Multi-signal |
| image)    |    | - Markup    |   |   scoring      |
+-----------+    | - Fees      |   +----------------+
                  |
                  v
            +-------------+
            | Explanation |
            |   Agent     |
            |  (Gemini)   |
            +-------------+

 4. Features Implemented (Capstone Requirements)
✔ Multi-Agent System

Orchestrator agent

QR parser agent

QR image agent

FX agent

Risk scoring agent

Explanation (LLM) agent

✔ Tools

Custom Tool: Live FX API

Custom Tool: QR image decoder

Built-in Tools: Gemini API (LLM)

HTTP client for external API

✔ Session & Memory

InMemorySessionService

SimpleMemoryBank

Merchant history

Risk preference memory

Context compaction

✔ Context Engineering

Dynamic system prompts

Conversation history compaction

Tool result summarization

✔ Observability

Logging using Python logging

Info + warning + error levels

✔ Evaluation

Included src/eval/run_eval.py

Runs QR test cases automatically

✔ Deployment Ready

Works with Render / Railway / Cloud Run

Listens on PORT

Environment variable key handling

 5. Installation (Local)
Clone the repo:
git clone https://github.com/YOUR_USERNAME/qr-payment-agent.git
cd qr-payment-agent

Create virtual environment:
python -m venv .venv


Activate:

Windows PowerShell:

.venv\Scripts\Activate.ps1


Mac/Linux:

source .venv/bin/activate

Install dependencies
pip install -r requirements.txt

Set your Gemini API key
$env:GEMINI_API_KEY="YOUR_KEY_HERE"

 6. Run Locally
Run CLI version
python -m src.main

Run Gradio UI
python -m src.ui.app


This opens a browser window:

Upload images

Paste text

View JSON + Explanation

See history
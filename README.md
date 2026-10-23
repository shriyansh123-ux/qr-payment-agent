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

## Security and correctness repair (October 2026)

The API now requires a developer-configured `QR_API_KEY` (at least 24 characters). Generate a key and set it in the **backend environment**, not in frontend source control:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:QR_API_KEY="PASTE_YOUR_GENERATED_KEY"
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

Start the React UI from `web/` with `npm install` followed by `npm run dev`. Enter the same developer key into the local form. This is suitable for **local testing only**: a shared key sent to a browser cannot protect a public multi-user service. For deployment, implement server-side per-user authentication, request limits, HTTPS, and a proxy that handles credentials securely. To run Gradio locally, use `python -m src.ui.app`; it calls the orchestrator directly and does not enforce API key authentication, so do not expose it publicly.

Supported **text** inputs: `QR:JP:JPY:1500` demonstrator strings and **amount-bearing UPI URIs** such as `upi://pay?pa=demo@upi&am=150.00&cu=INR`. Both are **unverified claims**; they do not validate or execute payments. Other QR formats, including many national and EMV payment QR standards, are not currently supported. Do not treat unrecognized formats as valid. Multi-QR demonstrator strings can be separated by commas or newlines.

FX results now use [Frankfurter dated reference rates](https://frankfurter.dev/) with a date/source field. They are **reference estimates**, not current bank/card quotes. If rates cannot be obtained, the API returns 503 instead of using invented 1:1/mock rates. The old nominal 3% markup and 11-unit fixed fee are no longer presented as a provider's actual charge; fees and spreads are **not quoted**. Transaction-size cautions are normalized to USD where rates are available. Risk labels are heuristic and cannot verify a recipient or predict fraud.

Run regression tests with `python -m pytest tests/test_repair_regression.py -q`. The older tests in `tests/` contain some assumptions about live network access and the previous unauthenticated routes; they need updating before the full suite can be considered green. External provider, Docker, and browser smoke tests must also be performed before any deployment.

Sensitive data: don't log or persist actual payee identifiers or raw payment QR strings. The repository already contains tracked development artifacts (bytecode, a sample SQLite database, and demo images); the new `.gitignore` prevents newly untracked copies but does not retroactively remove files from Git history. Review those artifacts manually for secrets or personal information before publication.

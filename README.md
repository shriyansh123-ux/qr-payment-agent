Universal Global QR Payment Translator Agent

A Multi-Agent, Gemini-Powered Financial Translator for Cross-Border QR Payments

This project is submitted as part of the Google AI Agent Builder Capstone.

It demonstrates a multi-agent AI system capable of reading international QR payment payloads, converting them to the user's home currency, computing fees, performing risk analysis, and producing a natural-language explanation powered by Gemini 2.5 Flash.

1. Problem Statement

QR payment systems are country-specific, each with its own:

currency

fee model

formatting rules

network charges

risk signals

For travelers, this creates friction:

How much will I actually pay in my home currency?

What network fees apply?

Is this merchant or transaction risky?

Should I proceed or cancel?

Traditional banking apps don't provide real-time, intelligent breakdowns.

2. Solution

Universal Global QR Payment Translator Agent

A multi-agent system that:

Reads QR payloads (e.g., QR:JP:JPY:1500)

Extracts country, currency, and amount

Converts amount into user’s home currency (INR)

Applies markups and network fees

Performs risk scoring

Uses Gemini 2.5 Flash to summarize and explain the final payable amount

Persists user preferences using memory (home currency, risk preference)

A complete conversational, intelligent financial assistant for global QR payments.

3. Key Features Demonstrated 

✔ 3.1 Multi-Agent System

QRParserAgent

FXRateAgent

RiskGuardAgent

OrchestratorAgent

✔ 3.2 Custom Tools

decode_qr_tool

fx_api_tool

fee_rules_tool

risk_data_tool

gemini_http_client (custom HTTPS tool)

✔ 3.3 Sessions & Memory

InMemorySessionService

SimpleMemoryBank

✔ 3,4 Context Engineering

Dynamic system prompt

Compact conversation history

Tool results → LLM prompt injection

✔ 3.5 Observability

Logging each step: QR decode, FX calculation, risk scoring

✔ 3.6 Gemini Integration

Uses official HTTP v1 endpoint

Model: gemini-2.5-flash

4. Architecture Diagram
                ┌──────────────────────────────────┐
                │     Universal QR Payment Agent   │
                └──────────────────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ Orchestrator    │
                      │  Agent          │
                      └─────────────────┘
                   /         |           \
                  /          |            \
                 ▼           ▼             ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ QRParser    │ │ FXRateAgent │ │ RiskGuard   │
        │  Agent      │ │             │ │   Agent     │
        └─────────────┘ └─────────────┘ └─────────────┘
                 │           │             │
                 ▼           ▼             ▼
       ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
       │ decode_qr   │ │ FX + fees   │ │ risk scoring │
       └─────────────┘ └─────────────┘ └──────────────┘
                      \      |       /
                       \     |      /
                        ▼    ▼     ▼
                   ┌──────────────────┐
                   │  Prompt Builder  │
                   └──────────────────┘
                               │
                               ▼
                  ┌──────────────────────┐
                  │ Gemini 2.5 Flash API │
                  │ (HTTP v1 tool call)  │
                  └──────────────────────┘
                               │
                               ▼
                  ┌────────────────────────┐
                  │ Final natural-language │
                  │  explanation returned  │
                  └────────────────────────┘

5. How to Install & Run
5.1 Clone this repo
git clone https://github.com/yourusername/qr-payment-agent.git
cd qr-payment-agent

5.2 Create venv
python -m venv .venv
.venv\Scripts\Activate.ps1

5.3 Install dependencies
pip install -r requirements.txt

5.4 Set environment variables
$env:GEMINI_API_KEY="YOUR_REAL_KEY"
$env:GEMINI_MODEL="gemini-2.5-flash"

5.5 Run
python -m src.main

6. Evaluation Script
python -m src.eval.run_eval
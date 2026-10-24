# QR Payment Agent — Cross-Currency QR Reference Translator

**Status: educational prototype, not a payment processor or fraud-verification system.** The app does not send money, authenticate merchants, or quote final bank/card charges.

The repository has a **React/Vite frontend**, **FastAPI backend**, a **standalone Gradio demo**, and a CLI. It demonstrates QR input parsing, indicative currency conversion, explainable transaction caution flags, and an optional Gemini explanation.

## Supported inputs

- Demo format: `QR:JP:JPY:1500`. Multiple demo strings can be separated with commas or newlines.
- Amount-bearing UPI payment URI: `upi://pay?pa=merchant@upi&am=100&cu=INR`.
- PNG, JPEG or WebP QR images up to 3 MiB and 12 megapixels (FastAPI upload limit).

This is **not** a generic decoder for every country's payment QR. EMV merchant-presented formats, dynamic no-amount UPI QR, and other schemes are not fully implemented. Demo QR strings have **no validated merchant identifier**; a payee address extracted from UPI is **unverified**.

## Local setup

Requires Python 3.13 and Node.js 22 or compatible versions.

1. Clone the repository and create a virtual environment.
2. Install API dependencies: `pip install -r requirements-api.txt`.
3. Generate a random development key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Store it locally in the backend's `QR_API_KEY` environment variable (at least 24 characters). **Never commit a key.**
4. Start the backend:
   - PowerShell: `$env:QR_API_KEY="YOUR_GENERATED_KEY"; python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000`
   - macOS/Linux: `QR_API_KEY="YOUR_GENERATED_KEY" python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000`
5. In a second terminal, run `cd web`, `npm ci`, then `npm run dev`.
6. Open `http://127.0.0.1:5173/` and enter the same local developer key into the form.

The app uses an `X-API-Key` header for this **local, single-user demo**. A shared secret entered into a browser **cannot securely authenticate multiple internet users**. Keep both interfaces on your local trusted network.

For the separate Gradio UI, install `pip install -r requirements.txt` and run `python -m src.ui.app`. The Gradio path calls the orchestrator directly and does **not** enforce the API's authentication. Do not expose Gradio publicly. CLI: `python -m src.main`.

## Calculations, risk flags, AI

The FX agent uses [Frankfurter](https://frankfurter.dev/) **dated reference rates**, first from its blended v2 feed and then (only if needed) from its ECB-backed v1 reference feed. Both enforce positive rates and publication dates no more than seven days old; neither is an executed payment-provider exchange rate. It returns its provider and observation date. It rejects unavailable or stale data rather than silently using made-up currency rates.

**Provider FX markups, card fees, payment network fees, and final payable amounts are unknown.** The response's `total_home` is the *reference conversion before provider fees*; nominal fee fields are placeholders with `fee_status: not_quoted`. It must not be represented as a final charge.

Risk scores are simple **caution heuristics**, primarily based on the USD-equivalent size and whether the purported merchant is identified. They are not fraud probabilities. If an additional USD conversion rate is unavailable, the transaction-size risk is `not_assessed`. Previously encountered payees and country codes alone do not prove safety.

Gemini is optional: supply `GEMINI_API_KEY` only in a trusted backend environment. Without it the orchestrator uses a deterministic explanation. The model is never responsible for the numerical rate calculation. Prompts avoid raw QR/payment addresses where possible.

## Tests and build

The repair pull request runs GitHub Actions jobs for:
- `python -m pytest tests/ -q` — offline tests, including generated real QR images and upload errors.
- `npm ci && npm run build && npm run lint && npm audit --audit-level=low` in `web/`.
- A live reference FX API request.
- Docker API startup and authenticated/unauthenticated smoke tests.
- Playwright/Chromium end-to-end local text scan, image scan, result display, and clear-history flow.

Run locally: `python -m pytest tests/ -q` (requires `pytest`, `httpx`, and `qrcode` in addition to API requirements).

The Dockerfile now builds the React frontend and serves it together with FastAPI at one origin; Gradio remains a separate local interface.

## Limitations / before production

- Replace the shared development API key with a real identity provider and per-user authorization.
- Add quotas/rate limiting, CSRF/abuse protection as appropriate, durable isolated user sessions, and secure payment-data handling.
- Integrate verified merchant identities, scheme-specific QR validators, bank/provider fee quotes, and authoritative risk signals if claiming real-world applicability.
- Independently confirm the payment recipient before authorizing a transaction in a trusted payment application.
- Review tracked historical development artifacts and any repository history for sensitive data. A `.gitignore` does not remove already committed files.
- Existing `src/persistence/history_store.py` is not wired to the React history view; the backend's session history is in memory and the React history table is browser state.

This project should be presented as an engineering prototype, not as a production-ready global QR-payment translator.


## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Windows PowerShell, Docker, and manually configured Render hosting instructions, environment variables, and security limitations.


## Step 4 — Privacy and reliability hardening

- Temporary backend sessions now expire after 30 minutes of inactivity, with at most 256 sessions per process. These are **single-process safeguards**, not durable multi-user isolation.
- The React app no longer stores the developer API key in `sessionStorage`; it stays in component memory until page reload. API keys still pass from the browser to the backend and **are not production-grade authentication**.
- React history no longer retains raw pasted QR strings or image filenames, and limits stored raw details to computed estimates and caution data. Clicking **Show Raw JSON** for the current result still exposes the parsed transaction in this browser session.
- Gemini's API key is now sent in the `x-goog-api-key` HTTP header, not as a query string. Error messages no longer include raw provider response bodies.
- These steps **do not** provide verified merchant identity, multi-user login, strong DDoS protection, or secure persistent storage. Treat hosted use as a synthetic-data educational demo.

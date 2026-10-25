# Running and deploying QR Payment Agent

This repository is an **educational reference-rate QR interpreter**, not a payment processor, bank integration, or fraud-verification product. Use only synthetic/demo payloads until stronger identity, storage and security controls are implemented.

## Requirements

- Python 3.13, Git and Node.js 22 (local development).
- Docker (optional, for one-container testing).
- A randomly generated development-only API key (at least 24 characters). Never commit secrets.

## Option A: local React + FastAPI

Open a PowerShell terminal in the repo root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-api.txt
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the generated value into this variable (never commit it):
$env:QR_API_KEY = "YOUR_RANDOM_KEY"
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000
```

Open a second terminal in the same repo root:

```powershell
cd web
npm ci
npm run dev
```

Visit `http://127.0.0.1:5173`. Enter the **same** key in the React form. The Vite dev server proxies requests from `/api` to `http://127.0.0.1:8000`. No frontend API URL or Vite build-time secret is needed.

Useful checks:

- `http://127.0.0.1:8000/api/health` responds with status `ok`.
- Submit `upi://pay?pa=merchant@upi&am=100&cu=INR`.
- Expected *reference* amount: INR 100 before provider fees, with an **unverified** payee.

Scan explanations are deterministic amount/rate breakdowns. No AI provider or Gemini credential is needed.

## Option B: unified Docker image

The Dockerfile compiles React using Node, then copies the static assets into the Python runtime. FastAPI serves the React UI from `/` and API from `/api` on **one HTTP origin**. Node is not present in the running production image.

```powershell
docker build -t qr-payment-agent:demo .
docker run --rm --name qr-agent-demo -p 127.0.0.1:8000:8000 -e QR_API_KEY="YOUR_RANDOM_KEY" qr-payment-agent:demo
```

Open `http://127.0.0.1:8000`. The container respects `PORT` if a hosting platform provides one.

If Docker is unavailable locally, GitHub Actions builds and smoke-tests the container for you.

## Option C: Render web service (manual demo deployment)

The root `render.yaml` is a Render Blueprint for **one Docker web service**, with a health check at `/api/health`, optional free-tier instance choice and `autoDeployTrigger: off`.

1. In the [Render dashboard](https://dashboard.render.com/), connect your GitHub account and select this repository.
2. Create a Blueprint using the repository's `render.yaml`, or create a Docker web service using the root `Dockerfile`.
3. Choose the `main` branch once the deployment pull request has been reviewed and merged.
4. Set **QR_API_KEY** in Render's environment settings to a new, independent randomly generated value. Do not place the value in GitHub, the Vite bundle, or `render.yaml`.
5. Use the `/api/health` check to confirm the backend starts, then load the Render service URL and perform a demo QR scan using the key you configured.
6. Confirm that the instance is Free before creating it. If unavailable, stop rather than provisioning a paid alternative.

No Render resources are created by merging this repository change. The Blueprint must be activated in a connected Render account. Automatic deployments are disabled in the provided Blueprint. Hosting requires provider account actions that are separate from GitHub permissions.

**Access boundary:** A Render web service has a public `onrender.com` endpoint. The QR demo uses a shared developer key; it is not individual user authentication. The separate account workspace uses expiring bearer tokens and user-scoped PostgreSQL summaries, with live isolation checks described in [the verification report](docs/VERIFICATION.md). It still lacks email verification, password recovery, MFA and mature session/device controls. Keep hosted registration disabled, do not circulate the developer key, and use synthetic data only. Broad public use requires a separate security review and stronger identity controls.

## Connecting Neon PostgreSQL to the existing Render service

The existing deployment was verified on 24 October 2026 with Render Free service `qr-payment-agent-demo` and Neon Free project `qr-payment-agent-db` in AWS Ohio. Reuse those resources; these steps are not instructions to create duplicates. No paid resources were provisioned during that setup.

1. Sign in to the authorized Neon account. Confirm the project is on Free. For a separate installation, choose Free explicitly and inspect the current limits before creating anything; do not add paid resources.
2. In the project's connection dialog, select the intended branch, database and role. Obtain the PostgreSQL URL privately with TLS enabled. Do not paste it in chat, commit it, or include it in screenshots.
3. Open the existing Render service's Environment settings. Set only `QR_DATABASE_URL` and `QR_ALLOW_REGISTRATION=false`. Preserve `QR_API_KEY`, `PORT` and unrelated variables. Merge key updates rather than replacing the whole variable collection.
4. Save and deploy the settings. Confirm the resulting deployment reaches **live**; saving configuration alone does not make it active.
5. Confirm `/api/health` returns `ok` and `/api/account/status` reports `enabled=true` and `registration_enabled=false`.
6. Verify actual PostgreSQL access. The status endpoint checks only whether a URL is configured. A synthetic login for a nonexistent user should return `401 Invalid credentials` after table initialization and a database query, rather than a database error. Cross-check the expected tables through Neon's SQL editor. Do not log credentials or connection strings while diagnosing failures.
7. With an authorized private synthetic account, verify a text scan saves a summary and that it returns after sign-out, page reload and sign-in. Keep registration disabled throughout hosted testing.

The app uses `qr_users`, `qr_tokens` and `qr_scan_summaries`; tables are initialized by account login/registration. Never use a SQLite file on Render's ephemeral filesystem for durable accounts. No Render PostgreSQL or Redis resource is required by this architecture.

For local account creation only, configure an isolated SQLite database and explicitly enable registration in that local process. Hosted private account provisioning is an operator action; there is no public signup or administrative account-management UI.

The repository Blueprint omits the Neon secret. Keep it in the existing service's secret configuration. Do not add a literal connection string to `render.yaml`, `.env` examples, frontend build variables, or documentation.

Free services may sleep or reach quotas. Review provider limits, retention and backup arrangements in their dashboards; the project does not promise permanent free availability or recovery guarantees.

## Technical defaults

| Setting | Purpose | Default |
| --- | --- | --- |
| `QR_API_KEY` | Required development API secret | Not configured; must set |
| `QR_DATABASE_URL` | Optional account database; use a TLS PostgreSQL URL on hosted deployments | Not configured by the repository; existing service configured privately |
| `QR_ALLOW_REGISTRATION` | Controls account creation | `false`; keep disabled on hosted service |
| `PORT` | Uvicorn HTTP listening port in Docker | 8000; Render config sets 10000 |
| `QR_CORS_ORIGINS` | Explicit cross-origin requests, if you add a separate frontend | Localhost dev origins |
| `VITE_API_BASE` | Optional API origin override for special deployments | Empty; same origin |

## Verification

CI runs Python tests, live FX checks, React build/lint/npm audit, Docker HTTP checks, bounded localhost load checks, and Chromium browser regressions. Coverage includes account/session behavior, per-QR conversion details and the user-entered fee calculator. See [docs/VERIFICATION.md](docs/VERIFICATION.md) for completed live checks and their limits. Results remain reference conversions, actual provider fees are unquoted, and merchant identifiers are unverified.

## Focused application scope

The interface is named **Travel QR Cost Estimator**. Risk scoring, the fixed recipient-unverified badge, AI calls, raw JSON views and browser-locale guessing are removed. Currency conversion, QR decoding, fee scenarios and optional private saved scans remain. Existing records and deployment secrets are preserved; the retired caution database column is not assessed or displayed. See [docs/SCOPE.md](docs/SCOPE.md).

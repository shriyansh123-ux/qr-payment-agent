# Step 3: Running and deploying QR Payment Agent

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

Gemini explanations are optional. Only set `GEMINI_API_KEY` in a trusted backend environment; no Gemini credential is required for core calculations.

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
6. If a free-tier instance is not available to your account, choose a plan deliberately and inspect cost details before creating resources.

No Render resources are created by merging this repository change. The Blueprint must be activated in a connected Render account. Automatic deployments are disabled in the provided Blueprint. Hosting requires provider account actions that are separate from GitHub permissions.

**Important security restriction:** A Render *web service* has a public `onrender.com` endpoint. This prototype does not have production identity-based authentication or meaningful multi-user data isolation. A shared key entered through a browser is **development access control, not public user authentication**. Do not use personal/real QR financial information or circulate the API key. For a wider external demo, add an authenticated access gateway **that blocks direct access to the origin**, or replace the development key with real login/session authorization before making it broadly accessible. If you cannot protect access, keep the demo on localhost.

## Technical defaults

| Setting | Purpose | Default |
| --- | --- | --- |
| `QR_API_KEY` | Required development API secret | Not configured; must set |
| `GEMINI_API_KEY` | Optional LLM explanation API | Not configured; deterministic fallback |
| `PORT` | Uvicorn HTTP listening port in Docker | 8000; Render config sets 10000 |
| `QR_CORS_ORIGINS` | Explicit cross-origin requests, if you add a separate frontend | Localhost dev origins |
| `VITE_API_BASE` | Optional API origin override for special deployments | Empty; same origin |

## Verification

CI runs Python tests, the live FX reference API check, React build/lint/npm audit, Docker container HTTP checks, and a real Chromium browser scan workflow against the combined app. The supported scope is **not** a globally interoperable payment QR system. Results are indicative reference conversions, provider fees are unquoted, and merchant identifiers are unverified.

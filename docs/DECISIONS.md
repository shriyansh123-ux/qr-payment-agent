# Architecture decisions

Short records of the choices that shaped the project, newest first. Each one says what was
decided, why, and what it costs.

## 7. Rename from "QR Payment Agent" to Travel QR Cost Estimator (November 2026)

**Decision.** Rename the repository, Python modules and UI. `src/agents` and
`src/orchestration` became `src/parsers` (QR text, EMV, image decoding) and `src/services`
(FX, currency catalog, the `CostEstimator`).

**Why.** The first version used LLM agents. After decision 4 nothing in the code was an
agent, so the name described a project that no longer existed and sent reviewers looking for
AI code.

**Cost.** Old links redirect on GitHub. The Render service keeps its old name so the hosted URL
is unchanged.

## 6. Public demo mode for synthetic payloads (November 2026)

**Decision.** Accept synthetic `QR:CC:CUR:amount` strings and manual conversion without the API
key (`QR_PUBLIC_DEMO=true`). UPI/EMV text and image uploads still need the key.

**Why.** With every feature behind a private key, a visitor to the hosted demo could only use
the cash helper. Demo strings carry no payee data, and the existing per-visitor rate limits
bound the cost of FX lookups.

**Cost.** Anyone can call the reference-rate provider through the app, up to the rate limit.

## 5. Money as `Decimal` rounded to each currency's minor unit (November 2026)

**Decision.** Amounts stay `Decimal` from parsing to the API response and are rounded to the
target currency's ISO 4217 minor unit: 0 places for JPY/KRW, 3 for KWD/BHD, 2 otherwise.

**Why.** Floats produce sums like 0.1 + 0.2 = 0.30000000000000004, and a fixed 2-place rounding
showed impossible amounts such as "JPY 1234.56". The cash helper already used integer minor
units; the QR flow now matches it.

## 4. Remove AI commentary, risk scoring and the "unverified recipient" badge (October 2026)

**Decision.** Delete the LLM client, risk scorer, caution labels and raw-JSON views. Keep
deterministic conversion details instead. See [SCOPE.md](SCOPE.md) for the full keep/remove list.

**Why.** The risk score was a transaction-size heuristic that looked like a safety check but
was not one, and AI text restated numbers the UI already showed. Both added latency, cost and
failure modes without answering the traveller's actual question: what will this cost me?

**Cost.** The `risk_level` column stays in the accounts table, filled with a placeholder, to
avoid a destructive migration.

## 3. Reference FX only, never an invented rate (October 2026)

**Decision.** Use Frankfurter's dated reference rates with an ECB fallback. Reject rates older
than seven days. If both feeds fail, return HTTP 503 rather than a hard-coded rate.

**Why.** A wrong number presented as an estimate is worse than an honest "unavailable". Every
result shows its rate, date and source so its age is visible.

## 2. No browser storage for keys, tokens or cash inputs (October 2026)

**Decision.** Keys, bearer tokens, demo history and cash counts live only in React state.

**Why.** A shared demo key in `localStorage` survives on shared or borrowed devices. Reloading
the page signs the visitor out, which is acceptable for a demo.

## 1. One container serving both the React build and the API (October 2026)

**Decision.** A multi-stage Dockerfile builds React with Node, then FastAPI serves `web/dist`
and `/api` from one origin.

**Why.** One free Render service instead of two, no CORS configuration in production, and a
strict `connect-src 'self'` content security policy.

# Verification summary

Documentation updated: **25 October 2026**. The checks below were completed on **24 October 2026**; they are a dated record, not continuous monitoring or a full security audit. No credentials, database URLs, token values, or private login files are included.

## Deployment and database

- Existing Render Free service: `qr-payment-agent-demo`.
- Neon Free PostgreSQL project: `qr-payment-agent-db`, AWS Ohio.
- Database URL saved privately as Render's `QR_DATABASE_URL`; existing `QR_API_KEY` and `PORT` preserved.
- Hosted registration explicitly kept disabled with `QR_ALLOW_REGISTRATION=false`.
- No paid resources were provisioned during setup and verification.
- Verified `/api/health` returned `ok`; configuration discovery reported accounts enabled and registration disabled.
- Verified connectivity beyond configuration discovery: a nonexistent synthetic login reached PostgreSQL table initialization and a user query before returning `Invalid credentials`. Neon SQL queries confirmed the three account tables.

## Private account behavior

| Check | Evidence / outcome |
| --- | --- |
| Sign-in and persistence | A private synthetic account signed in, saved an INR 100 summary, and retrieved it after sign-out, reload and sign-in |
| History visibility | Two separately authenticated accounts displayed only their own summaries |
| History clearing isolation | Controlled baseline: each account had one record (INR 111 and INR 200); clearing the second account left counts of 1 and 0, confirmed directly in PostgreSQL |
| Logout revocation | The first account's logout removed its token; its stored and active token counts were both 0 |
| Expiry enforcement | Deliberately expiring only the second synthetic account's tokens caused its protected scan request to be rejected; no scan was saved |

An earlier baseline record was absent during the initial clearing check, so the isolation conclusion uses the subsequently established and verified two-record controlled baseline. These checks demonstrate the exercised paths, not a complete authorization audit. Live logout verification inspected token removal; it did not directly replay the logged-out bearer token. The automated account test does exercise a request with a revoked token.

## Session UI fix — PR #8

[PR #8](https://github.com/shriyansh123-ux/qr-payment-agent/pull/8) was merged and deployed as commit `0facc7f218bbd75110050a0a02f86efbd936b53b`.

- Authenticated `401` responses clear local token, profile, password, history, result and old notices, then display the sign-in form.
- Incorrect login credentials remain a login error; ordinary service failures preserve the session.
- Successful logout shows an explicit signed-out notice; an unconfirmed server logout retains its warning.
- Live verification confirmed the corrected logout message and sign-in form after deliberately expiring a synthetic session. The earlier stale “Signed in” display is resolved.
- All six CI jobs passed, including browser regressions for expiry during scans, history clearing and initial history loading, incorrect login, ordinary service failure, and successful/failed logout.

## Explainable results and fee impact — PR #9

[PR #9](https://github.com/shriyansh123-ux/qr-payment-agent/pull/9) was merged and deployed as commit `9dd9e88f354c83ef1c7ccbad41645a903091bf4d`.

- Both workspaces show original amount, reference conversion, rate/date/source, caution reasons and an unverified-recipient label for each QR.
- The optional fee calculator validates markup and fixed-fee inputs. Assumptions remain in the page and are not added to saved summary history.
- Live arithmetic check: INR 100 with a 3% markup and INR 5 fixed fee displayed INR 108, including INR 8 added cost.
- The resulting Render deployment reached **live**. Health returned `ok`, registration remained disabled, and the service plan remained Free. The queried post-release error-log window returned no application error entries; this is not a claim about all historical logs.

All six jobs passed in [the feature CI run](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40108118423):

1. Python tests.
2. React build, lint and dependency audit.
3. Live reference FX checks.
4. Docker build and API smoke tests.
5. Bounded localhost load smoke checks.
6. Chromium browser regressions, including single/multi-QR explanations, provenance, caution details, fee arithmetic, invalid input, privacy and cleanup on session expiry.

The CI multi-QR UI fixture uses synthetic FX values to test rendering deterministically; it is not evidence of a real rate for that fixture. Separate live FX checks exercise the provider integration. The local Python runtime lacked pytest during the initial manual checks; the subsequent GitHub Actions Python and browser jobs passed.

## Scope and remaining work

This release is suitable for a controlled portfolio demonstration with synthetic data. It does not implement email verification, password recovery, MFA, mature session/device management, merchant verification, real payment execution, bank fee quotes or authoritative fraud signals. Email/recovery work was set aside when scope was narrowed to the core QR experience; no email service was provisioned.

Free-plan quotas, cold starts, backup/retention arrangements, stronger identity controls and a broader security review remain operator responsibilities before wider use. Do not interpret a low caution level as a verified recipient, or the fee scenario as an actual provider quote. Do not run load tests against the hosted Free service.

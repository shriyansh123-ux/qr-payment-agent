# Verification summary

Documentation updated: **25 October 2026**. The checks below were completed on **24–25 October 2026**; they are a dated record, not continuous monitoring or a full security audit. No credentials, database URLs, token values, or private login files are included.

## Current version at handoff

The implemented educational/portfolio scope is complete: supported QR reading, dated reference FX, fee scenarios, local payment simulation, six-currency cash assistance and private saved summaries. The latest deployed feature commit is `c42cf9b98effe12833fb0ec42e12730c380d28cf` (PR #16), verified on 25 October 2026. Its six CI jobs passed, including seven cash arithmetic tests. This documentation update does not rerun or extend that evidence.

Pending manual checks are physical-phone camera launch, on-device Thai/Devanagari/Arabic/Japanese rendering, a few uncoached usability walkthroughs and a presentation rehearsal. Do not report those as passed until performed. Real payments remain outside this version; provider onboarding is deferred rather than an outstanding completion requirement.

The sections below are release history. Risk/AI features described in earlier checks were removed in PR #12; see [SCOPE.md](SCOPE.md) and the [README](../README.md) for the current application.

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

Free-plan quotas, cold starts, backup/retention arrangements, stronger identity controls and a broader security review remain operator responsibilities before wider use. The former caution feature has been removed. The fee scenario is not an actual provider quote. Do not run load tests against the hosted Free service.


## Manual From/To converter — 25 October 2026

[PR #11](https://github.com/shriyansh123-ux/qr-payment-agent/pull/11) was merged and deployed as commit `56206228413fd32c164319870f741ab1c5b618fb`.

- Added a separate Currency converter workspace with From/To currency dropdowns, amount entry and swap.
- The live provider catalog loaded 159 recent currencies during verification. This count is dated and may change. Metals/reference units and historical-only entries are excluded; individual pair rates must still pass the existing freshness checks.
- Verified real USD-to-EUR and EUR-to-USD reference conversions. The deployed interface displayed the rate, date and source; swapping cleared the old estimate.
- All six jobs passed in [CI run 40169035239](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40169035239). New backend tests cover catalog filtering/caching, authentication, rounding, same-currency conversion, unsupported currencies, amount validation and provider failures. Browser checks cover list retry, both dropdowns, swap, stale-result cleanup, conversion errors and mobile overflow.
- Render deployment `dep-dbeq2khsrm7s73cvkaug` reached live. Health returned ok; account registration remained disabled. The queried post-release error-log window contained no application error entries.
- The converter reuses the existing private demo key and does not save conversion history, modify QR-encoded currencies, initiate payments, or provision paid resources. README instructions were updated with the feature.


## Focused cost estimator cleanup — 25 October 2026

[PR #12](https://github.com/shriyansh123-ux/qr-payment-agent/pull/12) was merged and deployed as commit `7d360733b1aafd94d2d925951c61eb4a6fafd819`. The interface is now named **Travel QR Cost Estimator**.

- Removed the fixed recipient-unverified badge, risk/caution displays, risk modules and their extra USD lookup, AI scan commentary/client, raw JSON/debug displays, browser-locale guessing and unused merchant/risk history helpers.
- Retained QR text/image reading, dated reference conversions, From/To currency selection, explicit fee scenarios, optional saved scans and their authentication/session protections. Reasons are documented in [SCOPE.md](SCOPE.md).
- Existing account records were preserved. The retired NOT NULL caution column remains as a schema compatibility detail, not an assessed or displayed feature. Account history no longer returns that field; scan results no longer include `risk_result`.
- All six jobs passed in [CI run 40170844281](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40170844281). New assertions verify same-currency scans make no external requests and that removed labels/debug views are absent, while conversion, fees, image decoding, history and sessions still work.
- Live Render deployment `dep-dbeqgv0ae00c73e0t210` reached live. A pre-existing synthetic account signed in, its older history remained readable, and a new INR 100 scan returned conversion details without recipient/risk/debug/locale features. The separate currency dropdowns loaded 159 entries during this check.
- Health returned ok, registration remained disabled and the service remained on Free. The queried post-deployment error-log window was empty. No paid resources or database schema deletion was performed.


## QR home currency and phone photos — 25 October 2026

[PR #13](https://github.com/shriyansh123-ux/qr-payment-agent/pull/13) was merged as `92a65f9a93438ef0c71ac627852183b46f23595b` and deployed in Render release `dep-dbeqsolg1s2s73dghnrg`, live at 07:23:51 UTC.

- QR text/image requests and private text scans accept an optional supported home currency. The encoded source amount/currency is preserved; the choice is per request and does not change another user's default. Each history row retains its target currency. Changing input clears the old result.
- Camera mode uses native photo capture with a rear-camera preference. It requests no continuous video or microphone stream. Unsupported browsers can use the image picker or text entry. Client and server enforce the supported image formats and upload limits.
- All six jobs passed in [CI run 40172397597](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40172397597), including 76 Python tests, React build/lint/audit, live FX, Docker/API, bounded local load and Chromium browser checks. New tests cover invalid/unsupported currency choices, original source preservation, image target propagation, account storage currency, catalog outages, camera photo upload and mixed-currency history.
- Live browser verification confirmed the deployed home-currency selector and Camera input. An existing private synthetic account converted JPY 1,500 to a USD reference estimate, saved a USD summary and retrieved it after logout, reload and sign-in. Its older INR summaries retained their currency. This exercises actual PostgreSQL reads/writes beyond the configuration flag.
- Health returned ok and registration remained disabled. The existing service was confirmed Free before release; no infrastructure or secret configuration was changed and no paid resources were created. The queried application-error window after deployment was empty.
- Physical phone camera launch and real-world photo decoding were not tested on a handset. CI verified a generated QR photo through the same upload/decode path; native capture behavior still depends on the phone/browser. No payment provider was onboarded and no payment execution was added.


## Local payment-flow simulation — 25 October 2026

[PR #14](https://github.com/shriyansh123-ux/qr-payment-agent/pull/14) was merged as `79ff73dbd48fc9cb8ec32b8a8f6bc6b7e2d821ef`. Render deployment `dep-dber95cs728c73d65a10` reached live at 07:50:19 UTC.

- Added an optional UI-only simulation after QR conversion: review reference amount and assumed fees, approve or cancel, show pending and a selected simulated success, decline or timeout. All stages explicitly say simulation. It opens no payment app, asks for no PIN/bank details and makes no provider requests.
- Fee or estimate changes reset the simulation. Its state is held only in React memory, never recorded as a payment or saved account status. This is an educational project demonstration, not a provider sandbox or payment integration.
- All six jobs passed in [CI run 40174110846](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40174110846). Chromium tests cover all outcomes, cancellation at review/pending, fee-change reset, invalid-fee removal, mobile overflow, zero simulation network requests, no browser storage and unchanged account-summary count.
- Live verification used an existing synthetic private account. INR 100 plus 3% markup and INR 5 fixed fee showed INR 108; approval moved to pending, then the selected successful simulation explicitly reported that no money moved. The saved scan count did not increase during the simulation.
- Health returned ok and account registration remained disabled. No backend, secret or infrastructure configuration was changed, no provider account was created, and no paid resources were provisioned. The queried post-release application-error window was empty.
- README and scope explain how to demonstrate the flow and distinguish it from future real payment integration.


## THB cash helper and local numeral recognition — 25 October 2026

[PR #15](https://github.com/shriyansh123-ux/qr-payment-agent/pull/15) was merged as `cccd56c5f55b52d74dc862951be9bf29bfdce8fb`. Render release `dep-dberiv8m7kps73eroio0` reached live at 08:11:16 UTC.

- Added a Cash helper workspace for Thai baht, the first supported cash currency. It displays everyday note/coin values with boxed Thai numeral equivalents, suggests exact payment and change combinations, and sums the quantities actually returned to identify matches, shortages and excess.
- Denominations were checked against the Bank of Thailand Series 17 page and Thailand government currency guide; official links and the checked date appear in the interface and README. Numeral boxes are equivalents, not note reproductions or authentication. Note/coin designs can vary. Other cash currencies are not implied by the FX catalog.
- All values use integer satang. The helper supports familiar and Thai-digit input, validates quantities and amounts, clears counted results after amount changes, rejects insufficient payment, and flags amounts not representable with listed everyday coins. No rounding rule is applied. Suggestions assume denomination availability rather than a known wallet inventory.
- Four local Node tests passed, including 4,001 combination value-conservation cases. All six jobs passed in [CI run 40175446374](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40175446374), with added cash arithmetic and Chromium coverage for alternative combinations, exact/short/extra change, invalid quantities, Thai input, insufficient payment, state reset, unrepresentable amounts and mobile layout. Browser tests confirmed the cash workspace sends no requests and writes no browser storage.
- Live verification: THB 117.75 paid with THB 500 gave expected change THB 382.25. A counted alternative using two 1-baht coins instead of the suggested 2-baht coin matched exactly. Removing one 25-satang coin produced a THB 0.25 shortfall; replacing it restored the match. Boxed Thai labels rendered beside familiar values.
- The cash workspace needs no API key or account and stores nothing. No backend, secret, registration or infrastructure changes were made. Health returned ok, registration remained disabled, and the queried post-release application-error window was empty. No paid resources were created.
- README, product scope and demo walkthrough now explain the cash feature and its THB-only scope.


## Six-currency cash catalogs — 25 October 2026

[PR #16](https://github.com/shriyansh123-ux/qr-payment-agent/pull/16) was merged as `c42cf9b98effe12833fb0ec42e12730c380d28cf`. Render release `dep-dberusnb9u1s73aomhkg` reached live at 08:36:42 UTC.

- Cash helper now offers THB, USD, EUR, JPY, INR and AED from separately reviewed local denomination catalogs. Each has its own source links, precision, local labels and availability/rounding guidance. Source details and explicit exclusions are recorded in [CASH_CURRENCIES.md](CASH_CURRENCIES.md).
- JPY accepts whole yen only. Decimal currencies use integer minor units. Supported digit input includes Thai, Devanagari, Arabic-script and full-width digits; the Arabic decimal separator is normalized. Local boxes are equivalents, not exact reproductions of every banknote series. USD/EUR use familiar value labels.
- Equal-value notes and coins have independent counters. Marked EUR 500 and INR 2000 notes can be counted but are excluded from suggestions. Switching currency clears amounts, quantities and results; it never relabels or converts prior cash amounts. No automatic cash rounding was introduced.
- Seven local cash tests passed. All six jobs passed in [CI run 40176870431](https://github.com/shriyansh123-ux/qr-payment-agent/actions/runs/40176870431), including catalog conservation, native input, whole yen, overlap/legacy handling and browser matching/short-change cases for every added currency. Browser checks retain no-request/no-storage and mobile-layout assertions.
- Live verification: EUR 17.60 paid with EUR 20 yielded a matching EUR 2.40 count; JPY 1175.50 was rejected while JPY 1175 paid with JPY 2000 yielded JPY 825. Switching to AED cleared the inputs. Arabic-script 117.75 paid with 200 yielded AED 82.25, and its counted return matched. Arabic-script local labels rendered in the denomination boxes.
- Health returned ok and registration remained disabled. The service was confirmed Free before deployment. No backend, secrets, registration or infrastructure configuration changed and no paid resources were added. The queried post-release application-error window was empty.
- README, scope and presentation guide were updated; the source-backed cash catalog is independent of the FX currency list.

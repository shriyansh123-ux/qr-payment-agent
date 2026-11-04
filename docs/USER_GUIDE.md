# User guide

Detailed behaviour of each workspace, supported inputs, configuration and known limits. For a quick overview see the [README](../README.md); for setup and hosting see [DEPLOYMENT.md](../DEPLOYMENT.md).

## Features

- **Text, image and phone-photo input:** amount-bearing UPI URIs, demo QR strings, and a restricted subset of EMV merchant-presented QR.
- **QR home-currency selection:** preserve the QR’s original amount/currency and choose the currency for the estimate. Demo text, images, phone photos and private text scans support this; saved summaries retain the actual target currency.
- **Manual currency converter:** separate From and To blocks, an amount input, provider-supported currency dropdowns and a swap button. Choose any listed pair; a fresh reference rate must still be available.
- **Conversion details:** original amount, reference conversion, exchange rate, publication date and source for each QR, including multi-QR results.
- **Fee exploration:** enter a percentage markup and fixed fee to see their illustrative impact. These assumptions stay in the page and are not saved to account history.
- **Payment-flow simulation:** review the estimate and assumed fees, simulate approval/cancellation and choose success/decline/timeout outcomes. It runs entirely in the page; no bank, payment app or provider is contacted and no payment status is saved.
- **Cash helper (THB, USD, EUR, JPY, INR, AED):** note/coin suggestions, boxed local numeral/word equivalents, expected change and a quantity counter for matching returned change. Runs in the page without a key.
- **Private accounts:** sign in, scan synthetic text QR data, and retrieve or clear only your own saved summaries.
- **Session handling:** tokens stay in React memory. Logout clears local account state; authenticated `401` responses return to sign-in and remove stale profile, history, results, and notices.

## Try the app

| Workspace | Access | What to demonstrate |
| --- | --- | --- |
| Cash helper | No key or sign-in | Choose one of six supported cash currencies, count notes/coins and check change |
| QR demo | None for `QR:` demo strings; private developer key for UPI/EMV text, images and photos | Read supported synthetic QR text or an image/photo and choose the home currency |
| Currency converter | None while public demo mode is on; otherwise the developer key | Choose From/To currencies and inspect the dated reference result |
| Saved scans | Separately provisioned private account | Scan synthetic text QR data and retrieve user-scoped summaries |

Start with **Cash helper → EUR**, enter bill **17.60** and handed-over amount **20**, then count one 2-euro coin and two 20-cent coins: the result should match **EUR 2.40**. No account or API key is needed for this flow. The payment simulation appears after a successful QR estimate and uses that workspace’s existing access; it asks for no additional credentials.

Public registration remains disabled. Keep private credentials out of screenshots and presentations. Use the [presentation guide](docs/DEMO_GUIDE.md) for the complete walkthrough.

## Cash payments and numeral recognition

Open **Cash helper** and select **Cash currency**: Thai baht (THB), US dollar (USD), euro (EUR), Japanese yen (JPY), Indian rupee (INR) or UAE dirham (AED). This reviewed cash catalog is independent of the larger FX currency catalog. Changing currency clears amounts and counted quantities; amounts are never relabelled or converted silently.

Enter the local cash bill, inspect one possible exact-payment combination, and enter the amount handed over (or try the next larger suggested note). The helper shows expected change and a possible denomination breakdown. Enter the quantities actually returned to identify a match, shortfall or excess. Any listed combination with the correct total passes. Note and coin counters stay separate even when they share the same face value.

Boxes show Thai, Devanagari, Arabic-script or Japanese numeral/word equivalents, and familiar value labels for USD/EUR. These are recognition aids, not reproductions or guarantees about every note/coin series. Familiar and supported local digits can be entered; Japanese full-width digits also work. Use a decimal point (or Arabic decimal separator), without grouping commas. Yen accepts whole units only; other supported currencies allow two decimal places.

Examples: **EUR 17.60** paid with **EUR 20** gives **EUR 2.40** change; **JPY 1,175** paid with **JPY 2,000** gives **JPY 825**. For Thai baht, bill **THB 117.75**, paid **THB 500**, expected change **THB 382.25**. An alternative combination with two 1-baht coins instead of one 2-baht coin is equally valid.

Arithmetic uses integer minor units, without FX or automatic rounding. Cash-rounding and small-coin availability depend on location; enter the actual agreed cash bill. Marked legacy notes can be counted but are excluded from suggestions. Suggestions assume denomination availability, not a known wallet inventory. No login/key is required, no cash details are sent to the server, and nothing is saved.

See [cash catalog, official sources and exclusions](docs/CASH_CURRENCIES.md), checked 25 October 2026. The selected currency's guidance and source links are also shown in the app. This catalog is not an exhaustive list of every historical valid design or a guarantee of merchant acceptance.

## Supported inputs

| Input | Synthetic example / scope |
| --- | --- |
| Demo QR | `QR:JP:JPY:1500` |
| Multiple demo QRs | `QR:JP:JPY:1500,QR:US:USD:12`, or newline-separated values |
| Amount-bearing UPI | `upi://pay?pa=merchant@upi&am=100&cu=INR` |
| EMV merchant QR | Restricted amount-bearing subset with mandatory fields, TLV validation and CRC-16 checksum |
| Images in QR demo | PNG, JPEG or WebP; API limits: 3 MiB, 12 megapixels, and 5,000 pixels per dimension |

Account mode supports **text scans**; image uploads remain in the QR demo. Dynamic UPI without an amount and arbitrary national QR schemes are unsupported. An EMV checksum detects accidental modification; it does not verify merchant identity or certify payment-scheme compatibility.

## Scan a phone photo

In **QR demo**, enter the private demo key, choose **Your home currency**, then open **Camera** and select **Take QR photo**. Supported mobile browsers offer the rear camera; desktop or unsupported browsers may open a file picker. Capture a clear, synthetic QR and select **Estimate cost**. This is photo capture followed by image decoding, not continuous live scanning. No microphone or background camera stream is requested. Only the selected image is uploaded; the API decodes it in memory and never writes it to disk. PNG/JPEG/WebP, 3 MiB and existing dimension limits apply; use a lower-resolution photo when needed. **Image** and **Text** remain available if capture is unavailable or permission is declined.

## Try the result breakdown

For manual conversion, open **Currency converter** (the demo key is optional while public demo mode is on), choose **From currency** and **To currency**, enter an amount and select **Convert**. Results show the reference rate, date and source. **Swap currencies** reverses the selected pair. Changing inputs clears the previous estimate.

The dropdown catalog is fetched from Frankfurter, cached for one hour and filtered to recent observations; historical-only entries and precious-metal/reference units are excluded. If the catalog or a fresh pair rate is unavailable, the app reports an error. This manual converter does not alter QR amounts, move money or save conversion history. QR scans preserve their encoded source currency. Select **Your home currency** to change the reference target; leaving it at default uses the configured home currency (INR on this deployment). Changing the selection clears the previous result, and each history row keeps its own currency.

1. Run locally, or use authorized private access to the hosted demo.
2. Scan `upi://pay?pa=merchant@upi&am=100&cu=INR`.
3. Inspect **Conversion details**: INR 100 original and reference amounts, a same-currency rate of 1, and the source/date of that conversion.
4. Open **Explore provider fees**. Enter 3% markup and INR 5 fixed fee.
5. The illustrated total is **INR 108**, including **INR 8** added cost.

Formula: `reference amount × (1 + markup / 100) + fixed fee`. For multiple QRs converted to the same currency, the percentage applies to the combined reference amount and the fixed fee is added **once**. This is not a per-transaction bank quote. Provider rounding, settlement rates and taxes may differ. Actual fees remain **not quoted**.

## Demonstrate the proposed payment flow

After scanning, optionally enter fees under **Explore provider fees**, then select **Start payment simulation**. Review the simulation total, choose **Demo outcome**, select **Approve simulation**, then **Show simulated result**. You can cancel during review or pending, or reset after a terminal state. Every stage is labelled simulation; it needs no PIN, bank information, provider account or business onboarding. Changing scan inputs, home currency or fees clears the old simulation. Multiple QR amounts are combined with the fixed fee added once.

The simulation is a UI prototype, not a provider sandbox or evidence of UPI/Apple Pay compatibility. No real payment requests, confirmations or receipts are produced. The [provider feasibility assessment](docs/PAYMENT_FEASIBILITY.md) is future commercial-integration research, not a requirement for presenting this educational project.

## Configuration

| Variable | Purpose |
| --- | --- |
| `QR_API_KEY` | Shared developer key; at least 24 characters; never publish it |
| `QR_DATABASE_URL` | SQLite URL locally, or TLS-enabled PostgreSQL URL for hosted accounts; server secret only |
| `QR_ALLOW_REGISTRATION` | Defaults to `false`; keep `false` on the hosted deployment |
| `QR_PUBLIC_DEMO` | Defaults to `true`: synthetic `QR:` strings and the converter work without a key |
| `QR_TRUSTED_PROXY_HOPS` | Reverse proxies in front of the app, for per-visitor rate limits; `1` on Render |
| `PORT` | Container listening port; preserve the existing Render setting |
| `REDIS_URL` | Optional shared throttle counters; no new resource is required |
| `QR_CORS_ORIGINS` | Explicit frontend origins when using separate origins |
| `VITE_API_BASE` | Optional public API-origin override; empty for same-origin hosting; never a secret |

Store the Neon connection string privately in Render as `QR_DATABASE_URL`, never in source, screenshots or examples. Preserve `QR_API_KEY` and `PORT` when updating database settings. See the [Neon connection procedure](DEPLOYMENT.md#connecting-neon-postgresql-to-the-existing-render-service).

## Accounts, privacy and sessions

Account endpoints use bearer authentication independently of the shared demo key:

- `POST /api/account/register` — only when registration is explicitly enabled.
- `POST /api/account/login` and `POST /api/account/logout`.
- `GET /api/account/me` and `GET /api/account/history`.
- `POST /api/account/scan-text` and `POST /api/account/clear-history`.
- `GET /api/account/status` — configuration discovery only; it does **not** prove database connectivity.

Passwords use salted scrypt. Random bearer tokens expire after one hour; only their SHA-256 digests are stored. Logout removes the current token. Browser reload clears the local token but does not itself revoke the server token. Failed logout clears local credentials and warns that server revocation was not confirmed.

Queries are parameterized. Account history is scoped to the authenticated user and stores timestamp, currency and derived total, excluding raw QR text and payee identifiers. Full breakdowns and fee assumptions are not saved in summary history. Account emails, password hashes and token digests still require appropriate database protection.

The QR demo's history is temporary browser state; the server keeps no per-visitor session for it. Neither developer keys nor account tokens are saved in browser local/session storage. Cash inputs and simulation states also stay only in React memory; they are not transmitted as cash/payment records or saved to account history.

## Reference rates

The FX agent uses [Frankfurter](https://frankfurter.dev/) dated reference rates: a blended v2 feed with an ECB-backed v1 fallback. It validates positive rates and publication dates no more than seven days old, rejecting future dates and unavailable/stale data. Same-currency conversion uses rate 1 and the current date. Neither feed is an executed payment-provider rate.

`total_home` is the reference conversion **before fees**. Backend fee fields are placeholders with `fee_status: not_quoted`; the UI calculator is a separate user-entered scenario.

Risk scoring, the recipient-verification badge, AI commentary, raw-JSON displays and browser-locale guessing have been removed. The scan flow performs the requested reference conversion without an extra USD risk lookup or AI request. Existing account data is preserved; a retired database column remains only for schema compatibility. See [the scope decisions](docs/SCOPE.md) for why each feature was kept or removed.

## Final manual checks

- [ ] On a physical phone, try Camera capture and the image/text fallbacks using synthetic QRs. Automated photo-upload tests do not prove handset camera behaviour.
- [ ] Check Thai, Devanagari, Arabic-script and Japanese labels on the phone, including small-screen inputs and quantity counting.
- [ ] Ask a few people to follow the QR, fee, cash-change and simulation flows without coaching; record confusing steps.
- [ ] Rehearse or record the demonstration with private credentials hidden.

These checks remain pending until actually performed. Optional improvements, such as carrying a scanned original amount into Cash helper, can wait for a later version.

## Remaining limitations

- No email verification, password recovery, MFA, or mature session/device management. These were not included in the focused release.
- Shared demo keys are developer access control, not individual identity. Private accounts provide scoped demo data, not production financial-service authentication.
- Throttling is best-effort: login 6/minute, registration 4/minute and scans 30/minute by client address/route. In-process counters reset with the service and are not a complete abuse defense.
- No merchant verification, payment execution, provider fee integration, or authoritative fraud signals.
- Free hosting/database quotas, cold starts, retention and backup arrangements need operator review before broader use.
- No claim of a full penetration test, regulatory certification, global QR interoperability, or production readiness.

The implemented feature scope is complete for a controlled portfolio project with synthetic data. Finish the manual checks above before claiming device-level or usability validation. Public registration remains disabled. Payment-provider onboarding is not required for this educational version.

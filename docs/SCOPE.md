# Product scope: Travel QR Cost Estimator

The original traveller problem is understanding a foreign merchant's amount in a familiar currency, estimating possible fees, and eventually paying through a supported provider. This application implements **cost estimation** and a clearly labelled, local-only **payment-flow simulation**. It does not determine payment-app eligibility, obtain a bank's final quote, or execute payment.

## Keep

| Function | Why it belongs |
| --- | --- |
| Read supported text/image QRs and phone photos | Extracts the amount and currency without manual retyping |
| Select home currency for QR estimates | Keeps the merchant’s encoded amount fixed while expressing the estimate in a familiar currency |
| From/To currency converter | Lets a traveller estimate values between supported currencies without needing a QR |
| Original amount, rate, date and source | Makes the calculation understandable and its age visible |
| User-entered fee scenario | Illustrates known markup/fixed-fee assumptions without inventing bank charges |
| Optional local payment-flow simulation | Demonstrates review, simulated approval, cancellation and outcomes for a project presentation without bank access or money movement |
| Cash helper and local numeral equivalents | Helps travellers count unfamiliar notes/coins and check change; uses reviewed THB/USD/EUR/JPY/INR/AED denomination sets, without FX or automatic rounding |
| Optional saved scans | Lets private users review prior reference amounts |
| Authentication, logout, expiry and user isolation | Protects those saved scans; these controls are not payment authorization |
| Validation, throttling and clear failure messages | Prevents invalid estimates and limits abuse on the free deployment |

## Remove

| Function | Why it was removed |
| --- | --- |
| Recipient-unverified badge | It was a fixed disclosure, not the result of an identity check; displaying it as a scan feature was confusing |
| Risk score, caution labels and reasons | Transaction-size heuristics do not establish safety or answer the traveller's cost question |
| Extra USD normalization for risk | It added a provider request unrelated to the requested conversion |
| AI scan commentary and its client | Deterministic conversion details explain the result without an AI dependency or repetitive fallback messages |
| Raw-JSON/debug views and detailed history notes | They clutter the user flow and may expose parsed QR data |
| Browser-locale region | Language preferences do not reliably indicate a traveller's current country |
| Unused merchant-history memory and risk-history component | They supported removed risk logic rather than the core use case |

Existing private accounts and saved records are preserved. The former `risk_level` database column remains solely to avoid a destructive schema migration; it is not assessed, displayed, or returned in account history. New records use a compatibility placeholder. The scan API no longer returns `risk_result`.

One plain boundary remains: reference estimates exclude actual provider charges; confirm the final amount in your payment app. The application does not make payments. This is necessary to describe what the calculation actually represents, not a verification feature.

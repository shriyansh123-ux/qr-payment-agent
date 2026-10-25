# Project explanation and three-minute demonstration

## What I built

Travel QR Cost Estimator is an educational travel cost and cash-payment helper for understanding a merchant’s price in a familiar currency and checking unfamiliar cash denominations and change. It reads supported payment QR formats, preserves the original amount, converts it using a dated reference exchange rate, and lets the user explore assumed provider fees. Its cash helper supports THB, USD, EUR, JPY, INR and AED with local value labels and exact change counting. A separate, clearly labelled simulation demonstrates the proposed payment journey without sending money.

## Why I built it

My starting question was: “When I travel abroad and scan a merchant’s QR, how much would this cost in my own currency after conversion and possible fees?”

The project explores that question by putting the original amount, reference conversion and fee assumptions in one flow. It also illustrates how a future payment approval experience could look. It does not claim a unique capability or validated market demand; testing with travellers would be needed to establish usefulness compared with tools they already use.

## What works and what is simulated

| Part | What the project actually does |
| --- | --- |
| QR input | Parses supported text or decodes an uploaded image/phone photo |
| Currency selection | Keeps the source currency from the QR; lets the user choose a home currency |
| FX | Requests a reference rate and displays its date and source; live requests can fail |
| Fee estimate | Calculates a percentage markup and fixed fee entered by the user |
| Cash helper | Counts listed notes/coins, suggests combinations, checks returned change and shows local numeral/word equivalents in six currencies |
| Private history | Stores derived scan summaries for separately provisioned private accounts |
| Payment demonstration | Local-only review, approval, cancellation and chosen success/decline/timeout states |
| Actual bank debit or merchant settlement | Future work; not implemented |

## Three-minute walkthrough

Before presenting, open the app and confirm it is awake. Use your existing authorized demo key or private account; keep credentials off slides and out of screen recordings. Public registration stays disabled. Use synthetic data. For a credential-free demonstration, start with Cash helper; QR and converter demonstrations require authorized access.

### 0:00–0:30 — Explain the problem

“A foreign-currency price is difficult to judge immediately. I wanted a traveller to see its value in their home currency, understand the fee assumptions, and preview a payment journey.”

### 0:30–1:15 — Show a foreign-currency estimate

In QR demo, choose INR as the home currency. Enter `QR:JP:JPY:1500` and select **Estimate cost**. In private Saved scans, use the same synthetic text and **Estimate and save summary**.

Point out the original JPY amount, converted INR estimate, rate, rate date and source. Do not memorise an INR value: the returned reference rate can change. Explain that this demo string is a test format, not a real Japanese merchant payment QR.

### 1:15–1:45 — Explain the fees

Open **Explore provider fees**. Enter 3% markup and a fixed fee of 5 in the chosen home currency.

“The app calculates reference amount × 1.03 + 5. These fees are assumptions I entered, not fees detected from the merchant or quoted by a bank.”

For a predictable arithmetic example, scan `QR:IN:INR:100` with INR selected: 3% plus INR 5 produces **INR 108**. This same-currency example demonstrates the calculation, not international conversion. For multiple QRs, the fixed fee is applied once to the combined estimate.

### 1:45–2:30 — Demonstrate the proposed payment journey

Select **Start payment simulation**, review the amount and choose **Simulated success**. Select **Approve simulation**, explain the pending stage, then select **Show simulated result**.

“The outcome is deliberately selected for demonstration. No bank or UPI app is contacted, and this is not a real payment confirmation.”

Reset and demonstrate cancellation or decline if time permits. No PIN, card number or bank login is needed.

### 2:30–3:00 — Explain the implementation and boundary

“React presents the interface. FastAPI parses supported QR data and requests reference FX. PostgreSQL stores private account summaries. The simulation stays in the browser and is not saved as a transaction.”

“The project demonstrates cost visibility and a proposed interaction. Real deductions would require an approved payment-provider integration and confirmed merchant, bank and app support.”

## Optional cash demonstration

Open **Cash helper** (no key required), select **THB**, enter bill THB 117.75, then try the 500-baht note. Show the expected THB 382.25 change, familiar values and boxed Thai numeral equivalents. Count three 100-baht notes, one 50, one 20, one 10-baht coin, two 1-baht coins and one 25-satang coin to match. Remove the 25-satang coin to demonstrate a THB 0.25 shortfall. Explain that other combinations with the same total also pass, and the helper supports THB, USD, EUR, JPY, INR and AED. Optionally select EUR and show EUR 17.60 paid with EUR 20 giving EUR 2.40 change. Changing currency clears the previous amounts and quantities.

## Questions I can answer

**Why not just use a currency converter?**  
The project starts with a supported QR, preserves the merchant amount, shows conversion provenance and combines it with explicit fee assumptions. A manual converter is also available.

**Does it deduct money through UPI or Apple Pay?**  
No. The payment journey is a labelled UI simulation. The app does not determine either payment method’s eligibility.

**Is the recipient verified?**  
The project performs no merchant identity verification and shows no verification badge. QR parsing or a checksum does not authenticate a merchant.

**Is the total exact?**  
It is exact only for the stated arithmetic and rounding assumptions. The bank’s final debit can use different rates, fees, taxes or rounding.

**Can it read every foreign QR?**  
No. It supports the documented restricted formats and amount-bearing inputs. Reading a format does not establish payment acceptance.

**What did I learn?**  
QR parsing and validation, API integration, reference FX provenance, integer cash arithmetic, fee scenarios, local numeral handling, React state management, private account history, session handling, automated testing and deployment.

## Current completion and remaining checks

The implemented feature set is complete for this version. Physical-phone camera behaviour, on-device script rendering and usability with a few people still need manual checks; automated browser tests are not a substitute. Rehearse or record this walkthrough with credentials hidden before presenting.

## Optional future work

First test the explanation and mobile photo flow with a few volunteers using synthetic QRs. Improve confusing steps based on their feedback. Treat real payment integration as a separate future project requiring provider access; business onboarding is not needed to present this prototype.

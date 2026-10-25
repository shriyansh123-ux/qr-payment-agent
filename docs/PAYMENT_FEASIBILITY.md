# International payment feasibility: India to UAE

Reviewed: **25 October 2026**. This is a public-documentation assessment, not an approved integration or a legal opinion.

## Decision

**Investigate Network International’s UAE UPI merchant-acceptance route as the first corridor. Do not implement a payment button yet.** Evidence supports participating UAE merchants accepting UPI; it does not establish access for this traveller-side application.

The app remains a reference-cost estimator. Provider onboarding, a supported integration channel, UPI-specific sandbox access and any costs require confirmation. No provider account, contract, sales enquiry or payment was submitted during this assessment, and no paid resources were created.

## Why this corridor

Network International documents UPI payments at its POS terminals, and NPCI’s July 2024 announcement describes a progressive UAE rollout. This matches an Indian traveller paying an overseas merchant from an Indian bank account. It does not mean every UAE merchant or every QR supports UPI. [Network alternate payment methods](https://www.network.ae/en/value-added-services/merchant/alternate-payment-methods), [NPCI announcement](https://www.npci.org.in/PDF/npci/press-releases/2024/NIPL-Press-Release-NPCI-International-partners-with-Network-International-to-enable-UPI-QR-payment-acceptance-across-its-merchants-in-the-UAE.pdf).

NPCI’s user flow requires international-payment activation, participating merchant acceptance, review of the foreign/INR amounts and charges, and authorization in the UPI app. Google Pay also limits this to eligible bank accounts and directs users to their bank for conversion fees. The estimator’s reference FX rate cannot replace the bank’s final debit quote. [NPCI UPI Global Acceptance](https://www.npci.org.in/product/upi-global-acceptance), [Google Pay UPI International](https://support.google.com/pay/india/answer/13949170?hl=en-GB).

## What the evidence establishes

| Capability | Finding | Consequence |
| --- | --- | --- |
| Indian traveller pays a participating UAE merchant by UPI | Documented for Network terminals | Suitable corridor to discuss with the provider |
| Any foreign QR becomes payable through UPI after conversion | Not established | Never rewrite a merchant QR into a generic UPI payment URI |
| Traveller app initiates a payment against another merchant’s terminal QR | No public integration contract found in the reviewed sources | Obtain explicit provider approval and technical documentation |
| Final INR amount, fees and quote validity are available to this app | Not established | Continue calling the existing output an estimate |
| General Network sandbox | Explicitly offered as a free test account | Application requires personal contact details and a business name |
| UPI International sandbox for this app’s role | Not confirmed | Generic card/AANI testing does not prove UPI testing |
| Zero-cost UPI-specific access and onboarding | Not confirmed; the general gateway test account is advertised free | Confirm that free access covers this UPI route and the app’s role |

N-Genius Online’s sandbox page documents account access and test scenarios including cards and AANI. **AANI is a separate payment method; its simulator is not evidence of UPI International support.** [Sandbox documentation](https://docs.ngenius-payments.com/reference/sandbox-test-environment).

The provider’s POS documentation describes merchant operations. Its Online API documentation must not be treated as a promise that the same APIs expose in-person UPI QR initiation. [In-person documentation](https://docs.ngenius-payments.com/docs/in-person-payments-overview).

## Questions ready for a provider discussion

These questions have not been sent.

1. Can a third-party traveller companion app initiate an India-to-UAE UPI International merchant payment, or is integration limited to contracted merchants, POS systems or PSPs?
2. Can the app resolve an existing Network terminal QR? Which QR schemas and sample payloads are authorized for testing? How is the merchant/outlet identity bound to the order?
3. Is there a **free UPI International sandbox**, with no paid subscription, production activation or minimum commitment? Please confirm UPI support separately from card and AANI simulators.
4. Does the integration expose the issuer’s final INR debit, exchange rate, charges, expiry and quote identifier, or must these be reviewed only inside the UPI app?
5. What approved app handoff/deep link is supplied, and which banks, apps, devices and merchant configurations are eligible?
6. Which authenticated server-side status API and callback mechanisms confirm success, failure, pending, expiry, reversal and refund? Can a traveller-side app access that merchant transaction status?
7. What business identity, merchant partnership, certification, security review, agreements and charges apply? Is a student prototype eligible?

## Implementation gate and test plan

Proceed only after the provider confirms the app’s role, corridor, free sandbox access and UPI-specific documentation. Credentials must go into server secret storage; never chat, frontend build values or source control.

The proposed flow is: supported merchant QR → provider eligibility/order resolution → provider quote if available → explicit user approval in the authorized payment app → server-confirmed outcome. A redirect or app return alone must not mark a payment successful.

Tests must cover mismatched merchant/order/amount/currency, expired quotes, denied or abandoned handoffs, pending outcomes, forged callbacks, duplicate/out-of-order events and recovery when callbacks are missed. Use the provider’s actual authentication and final-state rules. N-Genius Online currently documents callback whitelisting, single-attempt delivery and idempotent handling; those rules illustrate why polling/reconciliation matters, but must be reconfirmed for the specific UPI POS integration. [Webhook documentation](https://docs.ngenius-payments.com/reference/consuming-web-hooks).

## Gaps in this repository

- No payment-provider account, credentials, payment adapter, executable quote or status integration exists.
- The restricted EMV parser currently lacks AED numeric currency code 784. Adding the code alone would not establish Network QR compatibility; obtain approved synthetic payloads and test the complete schema first.
- Existing synthetic demo QRs prove parsing/conversion, not acceptance by a real merchant or bank.
- The private demo key and account login protect the prototype; they do not authorize bank debits.
- Camera mode is photo capture, not continuous scanning. Physical phone behavior remains a separate device check.

## Practical result

Public sources support the payment corridor. They do not establish a free self-service integration for this traveller-side app. The next external dependency is a provider response confirming eligibility, the exact API/SDK, approved sample QRs and UPI-specific sandbox access. Until then, keep the deployed cost estimator and avoid adding unverified compatibility labels or simulated payment success to its normal flow.


## Sandbox application follow-up

The [official test-account form](https://www.network.ae/en/test-account) explicitly offers a **free general gateway test account**. It requests first name, last name, email, mobile number and business name. No application was submitted and no personal data was transmitted. Whether an independent educational project qualifies, and whether the account includes UPI International, remain unanswered. Do not invent a registered business or infer UPI entitlement from generic sandbox access.

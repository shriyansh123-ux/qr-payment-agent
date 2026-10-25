# Cash currency catalog

Checked **25 October 2026**. This static, reviewed catalog is separate from the FX feed. It lists selected denominations for counting and suggestions, not every historical design, a legal-tender certification or a merchant-acceptance guarantee. No currency images are reproduced.

| Currency | Notes used in suggestions (major units) | Listed coins | Count-only notes |
| --- | --- | --- | --- |
| THB | 20, 50, 100, 500, 1000 | 25/50 satang; 1/2/5/10 baht | None |
| USD | 1, 2, 5, 10, 20, 50, 100 | 1/5/10/25/50 cents; 1 dollar | None |
| EUR | 5, 10, 20, 50, 100, 200 | 1/2/5/10/20/50 cents; 1/2 euros | 500 euros |
| JPY | 1000, 2000, 5000, 10000 | 1/5/10/50/100/500 yen | None |
| INR | 10, 20, 50, 100, 200, 500 | 50 paise; 1/2/5/10/20 rupees | 2000 rupees |
| AED | 5, 10, 20, 50, 100, 200, 500, 1000 | 1/5/10/25/50 fils; 1 dirham | None |

## Source records and important exclusions

- **THB:** [Bank of Thailand notes](https://www.bot.or.th/en/our-roles/banknotes/History-and-Series-of-Banknote-And-Commemorative/banknotes-series/banknote-series17.html), [Thailand government currency guide](https://thailand.go.th/page/thai-currency). Suggestions omit the 1/5/10 satang coins used outside everyday circulation.
- **USD:** [US Currency Education Program](https://www.uscurrency.gov/denominations), [US Mint specifications](https://www.usmint.gov/learn/coins-and-medals/circulating-coins/coin-specifications), [Treasury penny guidance](https://home.treasury.gov/news/featured-stories/penny-production-cessation-faqs). Pennies retain their value despite production cessation; actual availability and cash-rounding arrangements vary. Dollar coins and notes are separate counters.
- **EUR:** [ECB banknotes](https://www.ecb.europa.eu/euro/banknotes/current/html/index.en.html), [ECB coins](https://www.ecb.europa.eu/euro/coins/html/index.en.html), [Bank of Finland small-coin guidance](https://www.suomenpankki.fi/en/money-and-payments/euro-banknotes-and-coins/). The 500-euro note is retained for counting, excluded from suggestions because issuance stopped. National cash-rounding practices are not inferred from EUR alone.
- **JPY:** [Bank of Japan notes and coins in use](https://www.boj.or.jp/en/note_tfjgs/note/valid/). Amounts must be whole yen. The 2000-yen note is listed even though availability is not assumed.
- **INR:** [RBI currency FAQ, updated April 2025](https://rbi.org.in/scripts/FAQView.aspx?Id=136). The reviewed guidance retains the legal-tender status of the 2000-rupee note after withdrawal from circulation; it is count-only here. Older 1/2/5-rupee notes are outside this catalog. Withdrawn small coins and obsolete note designs are not endorsed. RBI coin acceptance limits are not enforced by this arithmetic aid.
- **AED:** [CBUAE circulated currency](https://centralbank.ae/en/our-operations/currency-and-coins/circulated-currency/). Small fils coins are listed but their presence at any shop is not assumed. Historical withdrawn designs are not validated by the face-value list.

## Numeral labels

Thai, Devanagari and Arabic-script digit labels are generated equivalents. JPY uses ordinary Japanese numeral/word equivalents, which can differ from formal banknote characters. USD/EUR retain familiar value labels; no fictional alternate numeral system is added. Labels do not identify or authenticate a particular series.

Amount input accepts familiar digits, Thai, Devanagari, Arabic-Indic/extended Arabic-Indic and full-width digits. Decimal currencies accept a dot or the Arabic decimal separator, with no grouping commas. Japanese kanji words are display aids, not a supported amount-input grammar.

## Calculation rules

- Use integer cents, satang, paise, fils or whole yen; never FX conversion.
- No rounding is applied. Enter the merchant-agreed cash bill.
- Return one possible combination, with unlimited listed denomination availability assumed. It is not a wallet inventory or an acceptance promise.
- Count all listed denominations, distinguishing note/coin IDs with equal values. Count-only legacy notes never appear in suggestions.
- Changing currency clears bill, paid amount, quantities and results rather than converting or relabelling them.
- All calculations stay in React memory. No cash API, login, browser storage or server persistence is used.
- Review official sources again before changing a denomination or its suggestion status. Add arithmetic and browser coverage for each currency, including precision, overlapping values and native labels.

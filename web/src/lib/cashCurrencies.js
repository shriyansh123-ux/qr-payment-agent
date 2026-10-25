// Hand-reviewed cash catalog. This is deliberately separate from the FX currency feed.
const denominations = (notes, coins, scale, legacy = []) => [
  ...notes.map(amount => ({ value: amount * scale, kind: "note" })),
  ...coins.map(value => ({ value, kind: "coin" })),
  ...legacy.map(amount => ({ value: amount * scale, kind: "note", suggest: false, detail: "Legacy / not suggested" })),
].map(item => ({ ...item, id: `${item.kind}-${item.value}` }))
  .sort((a, b) => b.value - a.value || (a.kind === "note" ? -1 : 1));

export const CASH_CURRENCIES = {
  THB: {
    code: "THB", name: "Thai baht", location: "Thailand", scale: 100, digits: 2,
    major: "baht", minor: "satang", nativeMajor: "บาท", nativeMinor: "สตางค์",
    numerals: "๐๑๒๓๔๕๖๗๘๙", lang: "th",
    denominations: denominations([1000, 500, 100, 50, 20], [1000, 500, 200, 100, 50, 25], 100),
    guidance: "Everyday coin suggestions start at 25 satang. The 1, 5 and 10 satang coins are excluded. No automatic rounding.",
    sources: [
      ["Bank of Thailand: notes", "https://www.bot.or.th/en/our-roles/banknotes/History-and-Series-of-Banknote-And-Commemorative/banknotes-series/banknote-series17.html"],
      ["Thailand government: coins", "https://thailand.go.th/page/thai-currency"],
    ],
  },
  USD: {
    code: "USD", name: "US dollar", location: "United States", scale: 100, digits: 2,
    major: "dollar", minor: "cent", nativeMajor: "dollars", nativeMinor: "cents", lang: "en",
    denominations: denominations([100, 50, 20, 10, 5, 2, 1], [100, 50, 25, 10, 5, 1], 100),
    guidance: "Pennies remain valid although circulating production has stopped. Availability and local cash-rounding practices vary; enter the agreed cash bill. Dollar coins, half dollars and $2 notes may be less familiar. No automatic rounding.",
    sources: [
      ["US Currency Education Program: notes", "https://www.uscurrency.gov/denominations"],
      ["US Mint: coin specifications", "https://www.usmint.gov/learn/coins-and-medals/circulating-coins/coin-specifications"],
      ["US Treasury: penny guidance", "https://home.treasury.gov/news/featured-stories/penny-production-cessation-faqs"],
    ],
  },
  EUR: {
    code: "EUR", name: "Euro", location: "Euro area", scale: 100, digits: 2,
    major: "euro", minor: "cent", nativeMajor: "€", nativeMinor: "euro cent", lang: "en",
    denominations: denominations([200, 100, 50, 20, 10, 5], [200, 100, 50, 20, 10, 5, 2, 1], 100, [500]),
    guidance: "The €500 note remains valid but is no longer issued: count it if received, but it is excluded from suggestions. Small-coin availability and cash rounding vary by country; enter the agreed cash bill. No automatic rounding.",
    sources: [
      ["European Central Bank: banknotes", "https://www.ecb.europa.eu/euro/banknotes/current/html/index.en.html"],
      ["European Central Bank: coins", "https://www.ecb.europa.eu/euro/coins/html/index.en.html"],
      ["Bank of Finland: small coins", "https://www.suomenpankki.fi/en/money-and-payments/euro-banknotes-and-coins/"],
    ],
  },
  JPY: {
    code: "JPY", name: "Japanese yen", location: "Japan", scale: 1, digits: 0,
    major: "yen", lang: "ja",
    localLabels: { 10000: "一万円", 5000: "五千円", 2000: "二千円", 1000: "千円", 500: "五百円", 100: "百円", 50: "五十円", 10: "十円", 5: "五円", 1: "一円" },
    denominations: denominations([10000, 5000, 2000, 1000], [500, 100, 50, 10, 5, 1], 1),
    guidance: "Use whole yen only. The boxes show ordinary Japanese numeral/word equivalents; actual note lettering can use formal characters. No fractional-yen cash or automatic rounding.",
    sources: [["Bank of Japan: notes and coins in use", "https://www.boj.or.jp/en/note_tfjgs/note/valid/"]],
  },
  INR: {
    code: "INR", name: "Indian rupee", location: "India", scale: 100, digits: 2,
    major: "rupee", minor: "paise", nativeMajor: "₹", nativeMinor: "पैसे",
    numerals: "०१२३४५६७८९", lang: "hi",
    denominations: denominations([500, 200, 100, 50, 20, 10], [2000, 1000, 500, 200, 100, 50], 100, [2000]),
    guidance: "₹2,000 notes were withdrawn from circulation but remain legal tender in the reviewed RBI guidance: count them if received, not in suggestions. Older ₹1/₹2/₹5 notes are outside this catalog. Smallest listed coin is 50 paise. Coin acceptance limits may apply; suggestions do not establish a merchant's obligation to accept them. No automatic rounding.",
    sources: [["Reserve Bank of India: currency and coin FAQs", "https://rbi.org.in/scripts/FAQView.aspx?Id=136"]],
  },
  AED: {
    code: "AED", name: "UAE dirham", location: "United Arab Emirates", scale: 100, digits: 2,
    major: "dirham", minor: "fils", nativeMajor: "د.إ", nativeMinor: "فلس",
    numerals: "٠١٢٣٤٥٦٧٨٩", lang: "ar",
    denominations: denominations([1000, 500, 200, 100, 50, 20, 10, 5], [100, 50, 25, 10, 5, 1], 100),
    guidance: "Small fils coins in the official catalog may not be available at a particular shop. Enter the agreed cash bill; the helper does not assume rounding or availability. Historical withdrawn note designs are not endorsed by the denomination list.",
    sources: [["Central Bank of the UAE: circulated currency", "https://centralbank.ae/en/our-operations/currency-and-coins/circulated-currency/"]],
  },
};

// Mirrors src/money.py: ISO 4217 currencies whose minor unit is not 2 places.
const ZERO_DECIMAL = new Set(["BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "PYG",
  "RWF", "UGX", "UYI", "VND", "VUV", "XAF", "XOF", "XPF"]);
const THREE_DECIMAL = new Set(["BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"]);

export function minorUnits(currency) {
  const code = String(currency || "").toUpperCase();
  if (ZERO_DECIMAL.has(code)) return 0;
  if (THREE_DECIMAL.has(code)) return 3;
  return 2;
}

/** "JPY 1500", "INR 100.00", "KWD 0.368" — or "Unavailable" for missing values. */
export function formatMoney(value, currency) {
  if (value === null || value === undefined || value === "") return "Unavailable";
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "Unavailable";
  return `${currency} ${amount.toFixed(minorUnits(currency))}`;
}

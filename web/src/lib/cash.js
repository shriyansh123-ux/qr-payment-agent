// Integer minor units throughout: cents, satang, paise, fils or whole yen.
import { CASH_CURRENCIES } from "./cashCurrencies.js";
const THB = CASH_CURRENCIES.THB;
export const THB_DENOMINATIONS = THB.denominations;
const DIGIT_SETS = ["๐๑๒๓๔๕๖๗๘๙", "٠١٢٣٤٥٦٧٨٩", "۰۱۲۳۴۵۶۷۸۹", "०१२३४५६७८९", "０１２３４５６７８９"];
export const toThai = value => String(value).replace(/[0-9]/g, digit => DIGIT_SETS[0][Number(digit)]);
export function toWestern(value) {
  let result = String(value);
  for (const digits of DIGIT_SETS) result = result.replace(new RegExp(`[${digits}]`, "g"), digit => String(digits.indexOf(digit)));
  return result.replace(/٫/g, ".");
}

export function parseCashAmount(value, currency = THB) {
  const text = toWestern(value).trim();
  const pattern = currency.digits === 0 ? /^\d{1,7}$/ : /^\d{1,7}(\.\d{1,2})?$/;
  if (!pattern.test(text)) return null;
  const [whole, fraction = ""] = text.split(".");
  const units = Number(whole) * currency.scale + (currency.digits ? Number(fraction.padEnd(2, "0")) : 0);
  return units <= 1000000 * currency.scale ? units : null;
}

export function parseQuantity(value) {
  const text = toWestern(value).trim();
  if (text === "") return 0;
  return /^\d{1,5}$/.test(text) && Number(text) <= 10000 ? Number(text) : null;
}

export function cashMoney(units, currency = THB) {
  const whole = Math.floor(units / currency.scale);
  return `${currency.code} ${whole}${currency.digits ? `.${String(units % currency.scale).padStart(2, "0")}` : ""}`;
}

export function denominationLabel({ value, kind }, currency = THB) {
  return value < currency.scale ? `${value} ${currency.minor} ${kind} (${cashMoney(value, currency)})`
    : `${value / currency.scale} ${currency.major} ${kind}`;
}

export function nativeLabel({ value }, currency = THB) {
  if (currency.localLabels) return currency.localLabels[value];
  const number = value < currency.scale ? value : value / currency.scale;
  const label = currency.numerals ? String(number).replace(/[0-9]/g, digit => currency.numerals[Number(digit)]) : String(number);
  return `${label} ${value < currency.scale ? currency.nativeMinor : currency.nativeMajor}`;
}

export function cashCombination(units, currency = THB) {
  if (!Number.isSafeInteger(units) || units < 0 || units > 1000000 * currency.scale) return null;
  let remaining = units;
  const result = currency.denominations.filter(item => item.suggest !== false).flatMap(denomination => {
    const quantity = Math.floor(remaining / denomination.value);
    remaining %= denomination.value;
    return quantity ? [{ ...denomination, quantity }] : [];
  });
  return remaining === 0 ? result : null;
}

export function countReturned(quantities, currency = THB) {
  let total = 0;
  for (const denomination of currency.denominations) {
    const count = parseQuantity(quantities[denomination.id] ?? "");
    if (count === null) return null;
    total += count * denomination.value;
  }
  return total;
}

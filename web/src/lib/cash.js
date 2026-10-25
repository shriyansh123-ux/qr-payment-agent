// Values are integer satang throughout. No FX, floating-point money arithmetic or rounding.
export const THB_DENOMINATIONS = [100000, 50000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 25]
  .map(value => ({ value, kind: value >= 2000 ? "note" : "coin" }));
const THAI = "๐๑๒๓๔๕๖๗๘๙";
export const toThai = value => String(value).replace(/[0-9]/g, digit => THAI[Number(digit)]);
export const toWestern = value => String(value).replace(/[๐-๙]/g, digit => String(THAI.indexOf(digit)));

export function parseCashAmount(value) {
  const text = toWestern(value).trim();
  if (!/^\d{1,7}(\.\d{1,2})?$/.test(text)) return null;
  const [whole, fraction = ""] = text.split(".");
  const units = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));
  return units <= 100000000 ? units : null;
}

export function parseQuantity(value) {
  const text = toWestern(value).trim();
  if (text === "") return 0;
  return /^\d{1,5}$/.test(text) && Number(text) <= 10000 ? Number(text) : null;
}

export function cashMoney(units) {
  return `THB ${Math.floor(units / 100)}.${String(units % 100).padStart(2, "0")}`;
}

export function denominationLabel({ value, kind }) {
  return value < 100 ? `${value} satang coin (THB ${(value / 100).toFixed(2)})`
    : `${value / 100} baht ${kind}`;
}

export function nativeLabel({ value }) {
  return value < 100 ? `${toThai(value)} สตางค์` : `${toThai(value / 100)} บาท`;
}

export function cashCombination(units) {
  if (!Number.isSafeInteger(units) || units < 0 || units > 100000000 || units % 25 !== 0) return null;
  let remaining = units;
  return THB_DENOMINATIONS.flatMap(denomination => {
    const quantity = Math.floor(remaining / denomination.value);
    remaining %= denomination.value;
    return quantity ? [{ ...denomination, quantity }] : [];
  });
}

export function countReturned(quantities) {
  let total = 0;
  for (const denomination of THB_DENOMINATIONS) {
    const count = parseQuantity(quantities[denomination.value] ?? "");
    if (count === null) return null;
    total += count * denomination.value;
  }
  return total;
}

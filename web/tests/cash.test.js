import test from "node:test";
import { CASH_CURRENCIES } from "../src/lib/cashCurrencies.js";
import assert from "node:assert/strict";
import { parseCashAmount, parseQuantity, cashCombination, countReturned, cashMoney,
  nativeLabel, THB_DENOMINATIONS, toThai, toWestern } from "../src/lib/cash.js";

test("cash decimals and Thai digits convert exactly into integer satang", () => {
  for (const [text, units] of [["117.75", 11775], ["0.25", 25], ["๕๐๐", 50000],
    ["๑๑๗.๗๕", 11775], ["1.1", 110], ["1000000.00", 100000000], ["0", 0]]) {
    assert.equal(parseCashAmount(text), units);
  }
  for (const text of ["", "-1", "1.001", "1e3", "Infinity", "NaN", "1,000", "1000000.01", "0x10"]) {
    assert.equal(parseCashAmount(text), null, text);
  }
  assert.equal(cashMoney(25), "THB 0.25");
  assert.equal(cashMoney(38225), "THB 382.25");
});

test("local numeral labels keep baht and satang distinct", () => {
  assert.equal(toThai("0123456789"), "๐๑๒๓๔๕๖๗๘๙");
  assert.equal(toWestern("๐๑๒๓๔๕๖๗๘๙"), "0123456789");
  assert.equal(nativeLabel({value:10000}), "๑๐๐ บาท");
  assert.equal(nativeLabel({value:25}), "๒๕ สตางค์");
  assert.equal(THB_DENOMINATIONS.length, 11);
});

test("exact payment and change suggestions conserve value", () => {
  for (let value = 0; value <= 100000; value += 25) {
    const combination = cashCombination(value);
    assert.equal(combination.reduce((sum, item) => sum + item.value * item.quantity, 0), value);
    assert.ok(combination.every(item => Number.isInteger(item.quantity) && item.quantity > 0));
  }
  assert.deepEqual(cashCombination(0), []);
  for (const value of [1, 10, 11760, -25, 25.5, 100000025, NaN]) {
    assert.equal(cashCombination(value), null);
  }
  const large = cashCombination(100000000);
  assert.equal(large[0].quantity, 1000);
});

test("different returned combinations match; short and extra stay exact", () => {
  const expected = parseCashAmount("500") - parseCashAmount("117.75");
  assert.equal(expected, 38225);
  const returned = {"note-10000":"3", "note-5000":"1", "note-2000":"1", "coin-1000":"1", "coin-100":"2", "coin-25":"1"};
  assert.equal(countReturned(returned), expected);
  assert.equal(countReturned({...returned, "coin-25":"0"}), expected - 25);
  assert.equal(countReturned({...returned, "coin-25":"2"}), expected + 25);
  assert.equal(countReturned({"coin-100":"๒", "coin-25":"๑"}), 225);
  assert.equal(countReturned({"coin-100":"1.5"}), null);
  assert.equal(countReturned({"coin-100":"-1"}), null);
  assert.equal(countReturned({"coin-100":"10001"}), null);
  assert.equal(parseQuantity(""), 0);
  assert.equal(parseQuantity("10000"), 10000);
  assert.equal(parseQuantity("1e2"), null);
});


test("all cash catalogs conserve integer value and have unique note/coin IDs", () => {
  assert.deepEqual(Object.keys(CASH_CURRENCIES).sort(), ["AED", "EUR", "INR", "JPY", "THB", "USD"]);
  for (const currency of Object.values(CASH_CURRENCIES)) {
    assert.equal(new Set(currency.denominations.map(item => item.id)).size, currency.denominations.length);
    assert.ok(currency.denominations.every(item => Number.isSafeInteger(item.value) && item.value > 0));
    const smallest = Math.min(...currency.denominations.filter(item => item.suggest !== false).map(item => item.value));
    for (let amount = 0; amount <= 10000; amount += smallest) {
      const combo = cashCombination(amount, currency);
      assert.notEqual(combo, null, currency.code);
      assert.equal(combo.reduce((sum, item) => sum + item.value * item.quantity, 0), amount, currency.code);
      const counts = Object.fromEntries(combo.map(item => [item.id, String(item.quantity)]));
      assert.equal(countReturned(counts, currency), amount, currency.code);
      assert.ok(combo.every(item => item.suggest !== false));
    }
    assert.equal(parseCashAmount("1000000", currency), 1000000 * currency.scale);
    assert.equal(parseCashAmount("1000001", currency), null);
  }
});

test("whole yen precision and numeral labels work without fictional cents", () => {
  const yen = CASH_CURRENCIES.JPY;
  assert.equal(parseCashAmount("１０００", yen), 1000);
  assert.equal(parseCashAmount("1500.50", yen), null);
  assert.equal(parseCashAmount("1500.00", yen), null);
  assert.equal(cashMoney(382, yen), "JPY 382");
  assert.equal(nativeLabel({value:1000}, yen), "千円");
  assert.equal(parseCashAmount("١١٧.٧٥", CASH_CURRENCIES.AED), 11775);
  assert.equal(parseCashAmount("١١٧٫٧٥", CASH_CURRENCIES.AED), 11775);
  assert.equal(parseCashAmount("११७.५०", CASH_CURRENCIES.INR), 11750);
  assert.equal(nativeLabel({value:10000}, CASH_CURRENCIES.INR), "१०० ₹");
  assert.equal(nativeLabel({value:10000}, CASH_CURRENCIES.AED), "١٠٠ د.إ");
});

test("overlapping note/coin values count independently; legacy notes are never suggested", () => {
  assert.equal(countReturned({"note-100":"2", "coin-100":"3"}, CASH_CURRENCIES.USD), 500);
  assert.equal(countReturned({"note-2000":"1", "coin-2000":"2"}, CASH_CURRENCIES.INR), 6000);
  for (const [code, value] of [["EUR", 50000], ["INR", 200000]]) {
    assert.equal(countReturned({[`note-${value}`]:"1"}, CASH_CURRENCIES[code]), value);
    assert.ok(cashCombination(value, CASH_CURRENCIES[code]).every(item => item.suggest !== false));
    assert.ok(!cashCombination(value, CASH_CURRENCIES[code]).some(item => item.id === `note-${value}`));
  }
  assert.equal(cashCombination(1, CASH_CURRENCIES.INR), null);
});

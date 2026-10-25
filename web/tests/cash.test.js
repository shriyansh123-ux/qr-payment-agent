import test from "node:test";
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
  const returned = {10000:"3", 5000:"1", 2000:"1", 1000:"1", 100:"2", 25:"1"};
  assert.equal(countReturned(returned), expected);
  assert.equal(countReturned({...returned, 25:"0"}), expected - 25);
  assert.equal(countReturned({...returned, 25:"2"}), expected + 25);
  assert.equal(countReturned({100:"๒", 25:"๑"}), 225);
  assert.equal(countReturned({100:"1.5"}), null);
  assert.equal(countReturned({100:"-1"}), null);
  assert.equal(countReturned({100:"10001"}), null);
  assert.equal(parseQuantity(""), 0);
  assert.equal(parseQuantity("10000"), 10000);
  assert.equal(parseQuantity("1e2"), null);
});

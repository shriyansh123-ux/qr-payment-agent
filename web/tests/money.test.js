import { test } from "node:test";
import assert from "node:assert/strict";
import { formatMoney, minorUnits } from "../src/lib/money.js";
import { isDemoPayload } from "../src/lib/qrFormats.js";

test("uses each currency's minor unit", () => {
  assert.equal(minorUnits("INR"), 2);
  assert.equal(minorUnits("jpy"), 0);
  assert.equal(minorUnits("KWD"), 3);
  assert.equal(formatMoney(1500, "JPY"), "JPY 1500");
  assert.equal(formatMoney(100, "INR"), "INR 100.00");
  assert.equal(formatMoney(0.368, "KWD"), "KWD 0.368");  // values arrive already rounded by the API
});

test("missing values are unavailable, not zero", () => {
  for (const value of [null, undefined, "", "abc", NaN]) assert.equal(formatMoney(value, "USD"), "Unavailable");
});

test("demo payload detection matches the server rule", () => {
  assert.ok(isDemoPayload("QR:JP:JPY:1500"));
  assert.ok(isDemoPayload("QR:JP:JPY:1500,QR:US:USD:12\nqr:th:thb:40.5"));
  assert.ok(!isDemoPayload("upi://pay?pa=merchant@upi&am=100&cu=INR"));
  assert.ok(!isDemoPayload("QR:JP:JPY:1500\nupi://pay?pa=a@b&am=1"));
  assert.ok(!isDemoPayload("QR:JP:JPY:1.234"));
  assert.ok(!isDemoPayload(""));
});

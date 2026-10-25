import { useId, useState } from "react";
import { THB_DENOMINATIONS, cashMoney, parseCashAmount, parseQuantity, cashCombination,
  countReturned, denominationLabel, nativeLabel } from "../lib/cash";

function Combination({ amount, label }) {
  const combination = cashCombination(amount);
  return <section className="cashSuggestion" aria-label={label}>
    <h3>{label}</h3>
    {combination === null ? <p>No exact combination with the listed everyday denominations. No rounding has been applied; confirm the cash bill with the merchant.</p>
      : combination.length === 0 ? <p>No cash change due.</p>
        : <ul>{combination.map(item => <li key={item.value}>
          <strong>{item.quantity} × {denominationLabel(item)}</strong>
          <span className="nativeNumeral" lang="th">{nativeLabel(item)}</span>
        </li>)}</ul>}
    <p className="hint">One possible combination. You or the cashier may use another combination with the same total; availability is not known.</p>
  </section>;
}

export default function CashHelper() {
  const id = useId();
  const [billInput, setBillInput] = useState("");
  const [paidInput, setPaidInput] = useState("");
  const [quantities, setQuantities] = useState({});
  const [counted, setCounted] = useState(false);
  const bill = parseCashAmount(billInput);
  const paid = parseCashAmount(paidInput);
  const billValid = bill !== null && bill > 0;
  const ready = billValid && paid !== null && paid >= bill;
  const expected = ready ? paid - bill : null;
  const received = countReturned(quantities);
  const nextNote = billValid ? [...THB_DENOMINATIONS].reverse().find(item => item.kind === "note" && item.value > bill) : null;
  function updateAmount(setter, value) {
    setter(value); setQuantities({}); setCounted(false);
  }
  return <section className="card cashHelper" aria-labelledby={`${id}-title`}>
    <h2 className="sectionTitle" id={`${id}-title`}>Cash helper</h2>
    <p className="hintText"><strong>Thailand · Thai baht (THB)</strong> — first supported currency. Check what to hand over and whether your returned notes and coins add up.</p>
    <p className="hint">1 baht = 100 satang. All amounts here are in THB, separate from FX estimates. Works without a demo key; calculations stay in this page.</p>
    <div className="cashAmounts">
      <label className="label" htmlFor={`${id}-bill`}>Bill amount (THB)
        <input className="textarea" id={`${id}-bill`} inputMode="decimal" value={billInput} maxLength={16}
          placeholder="Example: 117.75" onChange={event => updateAmount(setBillInput, event.target.value)} />
      </label>
      <label className="label" htmlFor={`${id}-paid`}>Amount handed over (THB)
        <input className="textarea" id={`${id}-paid`} inputMode="decimal" value={paidInput} maxLength={16}
          placeholder="Example: 500" onChange={event => updateAmount(setPaidInput, event.target.value)} />
      </label>
    </div>
    <p className="hint">Enter familiar or Thai digits, up to 1,000,000 THB and two decimal places. No automatic cash rounding.</p>
    {billInput !== "" && !billValid && <p role="alert">Enter a bill greater than zero, using at most two decimal places.</p>}
    {paidInput !== "" && paid === null && <p role="alert">Enter a valid amount handed over, using at most two decimal places.</p>}
    {billValid && paid !== null && paid < bill && <p role="alert">Payment is short by {cashMoney(bill - paid)}. No change is due yet.</p>}
    {billValid && <>
      <Combination amount={bill} label="Suggested exact payment" />
      {nextNote && <button className="btnSecondary" type="button" onClick={() => updateAmount(setPaidInput, (nextNote.value / 100).toFixed(2))}>
        Try paying with a {nextNote.value / 100} baht note
      </button>}
    </>}
    {ready && <>
      <p className="cashExpected" role="status">Expected change: <strong>{cashMoney(expected)}</strong></p>
      <Combination amount={expected} label="Suggested change" />
    </>}
    <h3>Recognise denominations and count returned change</h3>
    <p className="hintText">Match the familiar value to the Thai numeral box, then enter how many of each you received. These boxes show numeral equivalents, not reproductions of a particular note or coin. Designs and markings vary by series.</p>
    <div className="cashDenominations">
      {THB_DENOMINATIONS.map(item => {
        const invalid = parseQuantity(quantities[item.value] ?? "") === null;
        return <div className="cashDenomination" key={item.value}>
          <strong>{denominationLabel(item)}</strong>
          <span className="nativeNumeral" lang="th">{nativeLabel(item)}</span>
          <label htmlFor={`${id}-${item.value}`}>Quantity received: {denominationLabel(item)}</label>
          <input className="textarea" id={`${id}-${item.value}`} inputMode="numeric" maxLength={7}
            aria-invalid={invalid || undefined} value={quantities[item.value] ?? ""} placeholder="0" disabled={!ready}
            onChange={event => { setQuantities(previous => ({ ...previous, [item.value]: event.target.value })); setCounted(true); }} />
          {invalid && <p className="error">Use a whole quantity from 0 to 10,000.</p>}
        </div>;
      })}
    </div>
    {!ready && <p className="hint">Enter the bill and enough cash handed over to enable the change counter.</p>}
    {ready && counted && <div className="cashCheck" role="status">
      {received === null ? <p>Fix invalid quantities before checking the returned total.</p> : <>
        <p>Counted change: <strong>{cashMoney(received)}</strong></p>
        <strong>{received === expected ? "Change matches exactly." : received < expected
          ? `Change is short by ${cashMoney(expected - received)}.` : `Change is extra by ${cashMoney(received - expected)}.`}</strong>
      </>}
    </div>}
    <div className="actions"><button className="btnSecondary" type="button" onClick={() => { setQuantities({}); setCounted(false); }}>Clear counted change</button></div>
    <details className="cashSources"><summary>Denomination sources and scope</summary>
      <p>Checked 25 October 2026. Notes: 20, 50, 100, 500 and 1,000 baht. Everyday coins: 10, 5, 2, 1 baht and 50, 25 satang. The 1, 5 and 10 satang coins are excluded from everyday suggestions.</p>
      <p><a href="https://www.bot.or.th/en/our-roles/banknotes/History-and-Series-of-Banknote-And-Commemorative/banknotes-series/banknote-series17.html" target="_blank" rel="noreferrer">Bank of Thailand: banknotes</a>{" · "}
        <a href="https://thailand.go.th/page/thai-currency" target="_blank" rel="noreferrer">Thailand government: currency and coins</a></p>
      <p>Suggestions assume unlimited availability of the listed denominations. They do not inspect your wallet, authenticate cash, or apply a national rounding rule. Confirm any adjusted cash bill with the merchant.</p>
    </details>
  </section>;
}

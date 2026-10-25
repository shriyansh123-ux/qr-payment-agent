import { useId, useState } from "react";
import { CASH_CURRENCIES } from "../lib/cashCurrencies";
import { cashMoney, parseCashAmount, parseQuantity, cashCombination,
  countReturned, denominationLabel, nativeLabel } from "../lib/cash";

function Combination({ amount, label, currency }) {
  const combination = cashCombination(amount, currency);
  return <section className="cashSuggestion" aria-label={label}>
    <h3>{label}</h3>
    {combination === null ? <p>No exact combination with the listed everyday denominations. No rounding has been applied; confirm the cash bill with the merchant.</p>
      : combination.length === 0 ? <p>No cash change due.</p>
        : <ul>{combination.map(item => <li key={item.id}>
          <strong>{item.quantity} × {denominationLabel(item, currency)}</strong>
          <span className="nativeNumeral" lang={currency.lang} dir="auto">{nativeLabel(item, currency)}</span>
        </li>)}</ul>}
    <p className="hint">One possible combination. You or the cashier may use another combination with the same total; availability is not known.</p>
  </section>;
}

export default function CashHelper() {
  const id = useId();
  const [currencyCode, setCurrencyCode] = useState("THB");
  const currency = CASH_CURRENCIES[currencyCode];
  const money = value => cashMoney(value, currency);
  const [billInput, setBillInput] = useState("");
  const [paidInput, setPaidInput] = useState("");
  const [quantities, setQuantities] = useState({});
  const [counted, setCounted] = useState(false);
  const bill = parseCashAmount(billInput, currency);
  const paid = parseCashAmount(paidInput, currency);
  const billValid = bill !== null && bill > 0;
  const ready = billValid && paid !== null && paid >= bill;
  const expected = ready ? paid - bill : null;
  const received = countReturned(quantities, currency);
  const nextNote = billValid ? [...currency.denominations].reverse().find(item => item.kind === "note" && item.suggest !== false && item.value > bill) : null;
  function updateAmount(setter, value) {
    setter(value); setQuantities({}); setCounted(false);
  }
  return <section className="card cashHelper" aria-labelledby={`${id}-title`}>
    <h2 className="sectionTitle" id={`${id}-title`}>Cash helper</h2>
    <label className="label" htmlFor={`${id}-currency`}>Cash currency</label>
    <select className="textarea cashCurrencySelect" id={`${id}-currency`} value={currencyCode} onChange={event => {
      setCurrencyCode(event.target.value); setBillInput(""); setPaidInput(""); setQuantities({}); setCounted(false);
    }}>{Object.values(CASH_CURRENCIES).map(item => <option key={item.code} value={item.code}>{item.code} — {item.name} · {item.location}</option>)}</select>
    <p className="hintText"><strong>{currency.location} · {currency.name} ({currency.code})</strong>. Check what to hand over and whether your returned notes and coins add up.</p>
    <p className="hint">{currency.digits ? `1 ${currency.major} = ${currency.scale} ${currency.minor}.` : "Whole yen only."} All amounts here are in {currency.code}, separate from FX estimates. Works without a demo key; calculations stay in this page.</p>
    <p className="cashCurrencyGuidance">{currency.guidance}</p>
    <div className="cashAmounts">
      <label className="label" htmlFor={`${id}-bill`}>Bill amount ({currency.code})
        <input className="textarea" id={`${id}-bill`} inputMode={currency.digits ? "decimal" : "numeric"} value={billInput} maxLength={16}
          placeholder={currency.digits ? "Example: 117.75" : "Example: 1500"} onChange={event => updateAmount(setBillInput, event.target.value)} />
      </label>
      <label className="label" htmlFor={`${id}-paid`}>Amount handed over ({currency.code})
        <input className="textarea" id={`${id}-paid`} inputMode={currency.digits ? "decimal" : "numeric"} value={paidInput} maxLength={16}
          placeholder={currency.digits ? "Example: 500" : "Example: 2000"} onChange={event => updateAmount(setPaidInput, event.target.value)} />
      </label>
    </div>
    <p className="hint">Enter familiar or supported local digits, up to 1,000,000 {currency.code}. {currency.digits ? "Use at most two decimal places, with a decimal point (or Arabic decimal separator), without grouping commas." : "Use whole yen, without a decimal point."} No automatic cash rounding.</p>
    {billInput !== "" && !billValid && <p role="alert">Enter a bill greater than zero. {currency.digits ? "Use at most two decimal places." : "Use whole yen only."}</p>}
    {paidInput !== "" && paid === null && <p role="alert">Enter a valid amount handed over. {currency.digits ? "Use at most two decimal places." : "Use whole yen only."}</p>}
    {billValid && paid !== null && paid < bill && <p role="alert">Payment is short by {money(bill - paid)}. No change is due yet.</p>}
    {billValid && <>
      <Combination amount={bill} label="Suggested exact payment" currency={currency} />
      {nextNote && <button className="btnSecondary" type="button" onClick={() => updateAmount(setPaidInput, (nextNote.value / currency.scale).toFixed(currency.digits))}>
        Try paying with a {nextNote.value / currency.scale} {currency.major} note
      </button>}
    </>}
    {ready && <>
      <p className="cashExpected" role="status">Expected change: <strong>{money(expected)}</strong></p>
      <Combination amount={expected} label="Suggested change" currency={currency} />
    </>}
    <h3>Recognise denominations and count returned change</h3>
    <p className="hintText">Match the familiar value to the local label box, then enter how many of each you received. These boxes show numeral or word equivalents, not reproductions of a particular note or coin. Designs and markings vary by series.</p>
    <div className="cashDenominations">
      {currency.denominations.map(item => {
        const invalid = parseQuantity(quantities[item.id] ?? "") === null;
        return <div className="cashDenomination" key={item.id}>
          <strong>{denominationLabel(item, currency)}</strong>
          <span className="nativeNumeral" lang={currency.lang} dir="auto">{nativeLabel(item, currency)}</span>
          {item.detail && <span className="hint">{item.detail}</span>}
          <label htmlFor={`${id}-${item.id}`}>Quantity received: {denominationLabel(item, currency)}</label>
          <input className="textarea" id={`${id}-${item.id}`} inputMode="numeric" maxLength={7}
            aria-invalid={invalid || undefined} value={quantities[item.id] ?? ""} placeholder="0" disabled={!ready}
            onChange={event => { setQuantities(previous => ({ ...previous, [item.id]: event.target.value })); setCounted(true); }} />
          {invalid && <p className="error">Use a whole quantity from 0 to 10,000.</p>}
        </div>;
      })}
    </div>
    {!ready && <p className="hint">Enter the bill and enough cash handed over to enable the change counter.</p>}
    {ready && counted && <div className="cashCheck" role="status">
      {received === null ? <p>Fix invalid quantities before checking the returned total.</p> : <>
        <p>Counted change: <strong>{money(received)}</strong></p>
        <strong>{received === expected ? "Change matches exactly." : received < expected
          ? `Change is short by ${money(expected - received)}.` : `Change is extra by ${money(received - expected)}.`}</strong>
      </>}
    </div>}
    <div className="actions"><button className="btnSecondary" type="button" onClick={() => { setQuantities({}); setCounted(false); }}>Clear counted change</button></div>
    <details className="cashSources"><summary>Denomination sources and scope</summary>
      <p>Checked 25 October 2026. {currency.guidance}</p>
      <p>Sources: {currency.sources.map(([label, url], index) => <span key={url}>{index > 0 ? " · " : ""}<a href={url} target="_blank" rel="noreferrer">{label}</a></span>)}</p>
      <p>Suggestions assume unlimited availability of the listed denominations. They do not inspect your wallet, authenticate cash, or apply a national rounding rule. Confirm any adjusted cash bill with the merchant.</p>
    </details>
  </section>;
}

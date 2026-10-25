import { useEffect, useId, useState } from "react";
import { convertCurrency, getCurrencies } from "../lib/api";

export default function CurrencyConverter({ apiKey, onApiKeyChange }) {
  const id = useId();
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [catalogError, setCatalogError] = useState("");
  const [reload, setReload] = useState(0);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [amount, setAmount] = useState("1");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    getCurrencies().then(data => {
      if (!alive) return;
      if (!Array.isArray(data.currencies) || !data.currencies.length) throw new Error("No currencies available.");
      setCurrencies(data.currencies);
      const codes = data.currencies.map(item => item.code);
      setFrom(codes.includes("USD") ? "USD" : codes[0]);
      setTo(codes.includes("INR") ? "INR" : codes[0]);
      setLoading(false);
    }).catch(problem => {
      if (alive) { setCatalogError(problem.message || "Currency list unavailable."); setLoading(false); }
    });
    return () => { alive = false; };
  }, [reload]);

  function update(setter, value) {
    setter(value);
    setResult(null);
    setError("");
  }

  async function convert(event) {
    event.preventDefault();
    setResult(null);
    setError("");
    if (!apiKey.trim()) { setError("Enter your demo API key to convert."); return; }
    const value = Number(amount);
    if (!amount.trim() || !Number.isFinite(value) || value <= 0 || value > 1e12) {
      setError("Enter an amount greater than 0 and no more than 1,000,000,000,000."); return;
    }
    setBusy(true);
    try {
      setResult(await convertCurrency({ apiKey, amount, from_currency: from, to_currency: to }));
    } catch (problem) { setError(problem.message || "Conversion unavailable. Try again."); }
    finally { setBusy(false); }
  }

  return <section className="card" aria-labelledby={`${id}-title`}>
    <h2 className="sectionTitle" id={`${id}-title`}>Currency converter</h2>
    <p className="hintText">Choose the currency you have and the currency you want to estimate. This does not change the currency encoded in a QR.</p>
    <label className="label" htmlFor={`${id}-key`}>Demo API key</label>
    <input className="textarea" type="password" autoComplete="off" id={`${id}-key`} value={apiKey} disabled={busy}
      onChange={event => { onApiKeyChange(event.target.value); setResult(null); setError(""); }} />
    <p className="hint">Uses the same private demo key as the QR workspace. Held only in this page; never saved to browser storage.</p>
    {loading ? <p role="status">Loading supported currencies…</p> : catalogError ? <>
      <p role="alert">{catalogError}</p>
      <button className="btnSecondary" type="button" onClick={() => {
        setCatalogError(""); setLoading(true); setReload(value => value + 1);
      }}>Retry currency list</button>
    </> : <form onSubmit={convert}>
      <div className="conversionBlocks">
        <div className="conversionBlock">
          <h3>From</h3>
          <label className="label" htmlFor={`${id}-from`}>From currency</label>
          <select className="textarea" id={`${id}-from`} value={from} disabled={busy}
            onChange={event => update(setFrom, event.target.value)}>
            {currencies.map(item => <option key={item.code} value={item.code}>{item.code} — {item.name}</option>)}
          </select>
          <label className="label" htmlFor={`${id}-amount`}>Amount to convert</label>
          <input className="textarea" id={`${id}-amount`} type="number" min="0.000001" max="1000000000000" step="0.000001"
            required value={amount} disabled={busy} onChange={event => update(setAmount, event.target.value)} />
        </div>
        <div className="conversionBlock">
          <h3>To</h3>
          <label className="label" htmlFor={`${id}-to`}>To currency</label>
          <select className="textarea" id={`${id}-to`} value={to} disabled={busy}
            onChange={event => update(setTo, event.target.value)}>
            {currencies.map(item => <option key={item.code} value={item.code}>{item.code} — {item.name}</option>)}
          </select>
          <p className="label">Reference amount</p>
          <output className="convertedAmount" aria-live="polite">{result
            ? `${result.to_currency} ${Number(result.total_home).toLocaleString("en", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : "—"}</output>
        </div>
      </div>
      <div className="actions">
        <button className="btnSecondary" type="button" disabled={busy} onClick={() => {
          setFrom(to); setTo(from); setResult(null); setError("");
        }}>Swap currencies</button>
        <button className="btnPrimary" type="submit" disabled={busy}>{busy ? "Converting…" : "Convert"}</button>
      </div>
      <p className="hint">{currencies.length} provider-listed currencies with recent observations. Availability of a fresh rate still depends on the selected pair.</p>
    </form>}
    {error && <p className="error" role="alert">{error}</p>}
    {result && <div className="conversionDetails" role="status">
      <strong>{result.amount} {result.from_currency} = {Number(result.total_home).toFixed(2)} {result.to_currency}</strong>
      <p>Rate: 1 {result.from_currency} = {result.rate} {result.to_currency}</p>
      <p>Rate date: {result.rate_date} · Source: {result.provider === "same-currency" ? "Same currency; no FX conversion" : result.provider}</p>
    </div>}
    <p className="insightBoundary">Reference estimate before bank fees and markup. No money is moved, and this is not a final payment quote.</p>
  </section>;
}

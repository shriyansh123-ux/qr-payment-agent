import { useId, useState } from "react";
import PaymentSimulation from "./PaymentSimulation";

function money(value, currency) {
  const amount = Number(value);
  return value != null && Number.isFinite(amount)
    ? `${currency} ${amount.toFixed(2)}` : "Unavailable";
}

function FeeScenario({ amount, currency }) {
  const id = useId();
  const [percent, setPercent] = useState("0");
  const [fixed, setFixed] = useState("0");
  const markup = Number(percent);
  const fee = Number(fixed);
  const valid = percent.trim() !== "" && fixed.trim() !== "" &&
    Number.isFinite(markup) && markup >= 0 && markup <= 100 &&
    Number.isFinite(fee) && fee >= 0 && fee <= 1000000;
  const extra = amount * markup / 100 + fee;
  return <><details className="feeScenario">
    <summary>Explore provider fees</summary>
    <p className="hintText">Enter your provider’s markup and fixed fee. These are your assumptions; the QR does not quote them.</p>
    <div className="feeInputs">
      <label htmlFor={`${id}-markup`}>FX markup (%)
        <input className="textarea" id={`${id}-markup`} type="number" min="0" max="100" step="0.1"
          value={percent} onChange={event => setPercent(event.target.value)} />
      </label>
      <label htmlFor={`${id}-fixed`}>Fixed fee ({currency})
        <input className="textarea" id={`${id}-fixed`} type="number" min="0" max="1000000" step="0.01"
          value={fixed} onChange={event => setFixed(event.target.value)} />
      </label>
    </div>
    {valid ? <div className="feeEstimate" aria-live="polite">
      <span>Estimated total with your fees</span>
      <strong>{money(amount + extra, currency)}</strong>
      <span>Added cost: {money(extra, currency)}</span>
    </div> : <p role="alert">Enter a markup from 0 to 100% and a fixed fee from 0 to 1,000,000.</p>}
    <p className="hint">Illustration only. Provider rounding, taxes and settlement rates may differ. Nothing is charged or saved.</p>
  </details>
    {valid && <PaymentSimulation key={`${amount}-${currency}-${percent}-${fixed}`} amount={amount} currency={currency} fees={extra} />}
  </>;
}

export default function ScanInsights({ result }) {
  const id = useId();
  const items = (result?.multiple ? result.items : [result]) || [];
  const scans = items.filter(item => item?.fx_result);
  if (!scans.length) return null;
  const currency = scans[0].fx_result.to_currency;
  const totals = scans.map(item => item.fx_result.total_home);
  const canEstimate = currency && scans.every(item => item.fx_result.to_currency === currency) &&
    totals.every(value => value != null && Number.isFinite(Number(value)) && Number(value) > 0);
  const total = totals.reduce((sum, value) => sum + Number(value), 0);

  return <section className="scanInsights" aria-labelledby={`${id}-title`}>
    <div className="insightHeading">
      <h3 id={`${id}-title`}>Conversion details</h3>
    </div>
    <p className="hintText">Original amount, exchange rate and source for each QR.</p>
    {scans.map((item, index) => {
      const fx = item.fx_result;
      const qr = item.qr_info || {};
      const scheme = qr.raw_fields?.scheme || "Payment QR";
      return <article className="scanBreakdown" key={index} aria-label={`QR ${index + 1} breakdown`}>
        <div className="insightHeading">
          <h4>{scans.length > 1 ? `QR ${index + 1} · ` : ""}{scheme}</h4>
        </div>
        <dl className="insightFacts">
          <div><dt>Original amount</dt><dd>{money(qr.amount, fx.from_currency)}</dd></div>
          <div><dt>Reference conversion</dt><dd>{money(fx.total_home, fx.to_currency)}</dd></div>
          <div><dt>Exchange rate</dt><dd>{Number.isFinite(Number(fx.rate)) && fx.rate != null
            ? `1 ${fx.from_currency} = ${Number(fx.rate).toLocaleString("en", { maximumFractionDigits: 6 })} ${fx.to_currency}`
            : "Unavailable"}</dd></div>
          <div><dt>Rate date</dt><dd>{fx.rate_date || "Unavailable"}</dd></div>
          <div><dt>Rate source</dt><dd>{fx.provider === "same-currency" ? "Same currency · no FX conversion" : fx.provider || "Unavailable"}</dd></div>
          <div><dt>Provider fees</dt><dd>Not quoted</dd></div>
        </dl>
      </article>;
    })}
    <p className="hint">Estimates exclude actual provider charges. Confirm the final amount in your payment app; this app does not make payments.</p>
    {canEstimate && <FeeScenario amount={total} currency={currency} />}
  </section>;
}

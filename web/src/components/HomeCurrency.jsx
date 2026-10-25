import { useEffect, useId, useState } from "react";
import { getCurrencies } from "../lib/api";

export default function HomeCurrency({ value, onChange, disabled }) {
  const id = useId();
  const [currencies, setCurrencies] = useState([]);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    getCurrencies().then(data => {
      if (!Array.isArray(data.currencies) || !data.currencies.length) throw new Error();
      if (active) setCurrencies(data.currencies);
    }).catch(() => {
      if (active) setError("Currency list unavailable. You can still scan using the default home currency.");
    });
    return () => { active = false; };
  }, [retry]);
  return <div className="homeCurrency">
    <label className="label" htmlFor={id}>Your home currency</label>
    <select className="textarea" id={id} value={value} disabled={disabled} onChange={event => onChange(event.target.value)}>
      <option value="">Default home currency (INR on this demo)</option>
      {currencies.map(item => <option key={item.code} value={item.code}>{item.code} — {item.name}</option>)}
    </select>
    <p className="hint">The merchant’s amount and source currency come from the QR. This choice changes only the reference estimate.</p>
    {error && <><p role="status">{error}</p><button className="btnSecondary" type="button" disabled={disabled} onClick={() => {
      setError(""); setRetry(previous => previous + 1);
    }}>Retry currencies</button></>}
  </div>;
}

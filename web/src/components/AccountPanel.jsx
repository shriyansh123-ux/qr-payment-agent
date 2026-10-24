import { useEffect, useState } from "react";
import {
  accountStatus, accountRegister, accountLogin, accountLogout,
  accountHistory, accountClearHistory, accountScanText,
} from "../lib/api";

const SAMPLE = "upi://pay?pa=merchant@upi&am=100&cu=INR";

function formatMoney(value, currency) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return "Unavailable";
  return `${currency || "INR"} ${amount.toFixed(2)}`;
}

export default function AccountPanel({ userCountry }) {
  const [status, setStatus] = useState(null);
  const [statusError, setStatusError] = useState("");
  const [action, setAction] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState("");
  const [qrText, setQrText] = useState(SAMPLE);
  const [rows, setRows] = useState([]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    accountStatus().then(value => { if (alive) setStatus(value); })
      .catch(() => { if (alive) setStatusError("Account service unavailable."); });
    return () => { alive = false; };
  }, []);

  async function refreshHistory(currentToken) {
    const saved = await accountHistory(currentToken);
    setRows(saved.items || []);
  }

  async function authenticate(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setBusy(true);
    try {
      if (action === "register") {
        await accountRegister(email, password);
        setAction("login");
        setMessage("Test account created. Sign in to continue.");
      } else {
        const session = await accountLogin(email, password);
        const currentToken = session.access_token;
        // No browser storage. Reloading clears this credential.
        setToken(currentToken);
        setProfile(email.trim().toLowerCase());
        setPassword("");
        await refreshHistory(currentToken);
        setMessage("Signed in for this tab. Use synthetic QR data only.");
      }
    } catch (problem) {
      setError(problem.message || "Account action failed.");
    } finally {
      setBusy(false);
    }
  }

  async function scan() {
    if (!qrText.trim()) { setError("Enter QR text."); return; }
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const response = await accountScanText(token, qrText.trim(), userCountry);
      setResult(response);
      await refreshHistory(token);
    } catch (problem) {
      setError(problem.message || "Scan failed.");
    } finally {
      setBusy(false);
    }
  }

  async function clearHistory() {
    setBusy(true);
    setError("");
    try {
      await accountClearHistory(token);
      setRows([]);
      setResult(null);
      setMessage("Saved account history cleared.");
    } catch (problem) {
      setError(problem.message || "Unable to clear history.");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setError("");
    try {
      await accountLogout(token);
    } catch {
      // Clear local credentials regardless, but do not claim server revocation.
      setMessage("Signed out of this tab; server revocation was not confirmed.");
    } finally {
      setToken("");
      setProfile("");
      setRows([]);
      setResult(null);
      setPassword("");
      setBusy(false);
    }
  }

  if (statusError) return <section className="card" aria-label="Account workspace">
    <h2 className="sectionTitle">Account workspace</h2>
    <p role="alert">{statusError} The local demo remains available.</p>
  </section>;

  if (!status) return <section className="card" aria-label="Account workspace">
    <h2 className="sectionTitle">Account workspace</h2>
    <p>Checking account availability…</p>
  </section>;

  if (!status.enabled) return <section className="card" aria-label="Account workspace">
    <h2 className="sectionTitle">Account workspace</h2>
    <p className="hintText">Account mode is not enabled on this deployment. Connect a durable PostgreSQL database using a server-side environment variable to enable it. The QR demo remains available.</p>
    <p className="hint">Registration and persistent history are intentionally disabled without configured storage. No paid services are needed for local SQLite development.</p>
  </section>;

  return <section className="card" aria-label="Account workspace">
    <h2 className="sectionTitle">Account workspace</h2>
    <p className="hintText">Educational account demo. No real card details or payment credentials. Sessions are held only in memory in this browser tab.</p>
    {error ? <p className="error" role="alert">{error}</p> : null}
    {message ? <p className="accountNotice" role="status">{message}</p> : null}
    {!token ? <>
      <div className="tabs" role="group" aria-label="Account action">
        <button className={`tab ${action === "login" ? "active" : ""}`} type="button" onClick={() => setAction("login")}>Sign in</button>
        {status.registration_enabled && <button className={`tab ${action === "register" ? "active" : ""}`} type="button" onClick={() => setAction("register")}>Create test account</button>}
      </div>
      <form onSubmit={authenticate} className="accountForm">
        <label className="label" htmlFor="account-email">Email for test account</label>
        <input id="account-email" className="textarea" type="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} required maxLength={254}/>
        <label className="label" htmlFor="account-password">Password (at least 12 characters)</label>
        <input id="account-password" className="textarea" type="password" autoComplete={action === "register" ? "new-password" : "current-password"} value={password} onChange={e => setPassword(e.target.value)} minLength={12} required />
        <button className="btnPrimary" disabled={busy} type="submit">{busy ? "Working…" : action === "register" ? "Register" : "Sign in"}</button>
      </form>
    </> : <>
      <div className="accountBar">
        <span>Signed in: <strong>{profile}</strong></span>
        <button className="btnSecondary" type="button" disabled={busy} onClick={signOut}>Sign out</button>
      </div>
      <div className="form">
        <label className="label" htmlFor="account-qr">Synthetic QR text</label>
        <textarea className="textarea" id="account-qr" rows={3} value={qrText} onChange={e => setQrText(e.target.value)} />
        <p className="hint">Text scans currently supported in account mode. The demo workspace also supports images.</p>
        <button className="btnPrimary" type="button" disabled={busy} onClick={scan}>Translate and save summary</button>
      </div>
      {result && <div className="accountResult" role="status">
        <strong>Reference estimate:</strong> {result.multiple
          ? formatMoney(result.total_home, "INR")
          : formatMoney(result.fx_result?.total_home, result.fx_result?.to_currency)}
        <p className="hint">Indicative exchange rate, not a payment quote. No merchant identity is verified.</p>
      </div>}
      <div className="accountBar">
        <h3>Stored summary history</h3>
        <button type="button" className="btnSecondary" disabled={busy || !rows.length} onClick={clearHistory}>Clear saved history</button>
      </div>
      {rows.length === 0 ? <p>No saved summaries yet.</p> :
        <div className="tableWrap"><table className="table accountTable">
          <thead><tr><th>Time</th><th>Currency</th><th>Reference total</th><th>Caution</th></tr></thead>
          <tbody>{rows.map((row, index) => <tr key={`${row.timestamp}-${index}`}>
            <td>{new Date(row.timestamp * 1000).toLocaleString()}</td>
            <td>{row.currency}</td><td>{formatMoney(row.total_home, row.currency)}</td>
            <td>{row.risk_level}</td>
          </tr>)}</tbody>
        </table></div>}
    </>}
  </section>;
}

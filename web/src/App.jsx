import { useMemo, useState } from "react";
import "./App.css";
import { scanImage, scanText, clearHistory } from "./lib/api";
import AccountPanel from "./components/AccountPanel";
import ScanInsights from "./components/ScanInsights";
import CurrencyConverter from "./components/CurrencyConverter";
import HomeCurrency from "./components/HomeCurrency";
import QRPhoto from "./components/QRPhoto";
import CashHelper from "./components/CashHelper";

const USER_ID = "user-123";

function formatMoney(x, currency) {
  if (x === null || x === undefined || x === "") return "Unavailable";
  const n = Number(x);
  if (!Number.isFinite(n)) return "Unavailable";
  return `${currency} ${n.toFixed(2)}`;
}

function extractTotalINR(result) {
  if (!result || result.error) return null;

  // multi
  if (result.multiple && typeof result.total_home === "number") return result.total_home;

  // single
  const fx = result.fx_result;
  if (fx && typeof fx.total_home === "number") return fx.total_home;

  return null;
}

export default function App() {
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [workspace, setWorkspace] = useState("demo");
  const [mode, setMode] = useState("text"); // "text" | "image"
  const [qrText, setQrText] = useState("QR:JP:JPY:1500");
  const [imageFile, setImageFile] = useState(null);
  const [homeCurrency, setHomeCurrency] = useState("");

  const [sessionId, setSessionId] = useState(""); // backend will return real session id

  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totalINR = useMemo(() => extractTotalINR(result), [result]);
  const resultCurrency = result?.home_currency || result?.fx_result?.to_currency || "INR";

  function changeMode(next) {
    setMode(next); setImageFile(null); setResult(null); setError("");
  }

  function pushHistoryRow(inputLabel, resObj) {
    const t = new Date();
    const time = t.toLocaleTimeString();

    const row = {
      time,
      input: inputLabel,
      total: extractTotalINR(resObj),
      currency: resObj.home_currency || resObj.fx_result?.to_currency || "INR",
    };

    setHistory((prev) => [row, ...prev]);
  }

  async function onTranslate() {
    setError("");
    setLoading(true);
    setResult(null);

    try {
      let res;

      if (mode === "text") {
        const payload = (qrText || "").trim();
        if (!payload) throw new Error("Please enter QR text.");
        res = await scanText({
          apiKey: apiKeyInput,
          user_id: USER_ID,
          session_id: sessionId,
          qr_payload: payload,
          home_currency: homeCurrency,
        });
        setSessionId(res.session_id || sessionId);
        setResult(res);
        pushHistoryRow("Text QR (hidden)", res);
      } else {
        if (!imageFile) throw new Error("Please choose a QR image file.");
        res = await scanImage({
          apiKey: apiKeyInput,
          user_id: USER_ID,
          session_id: sessionId,
          file: imageFile,
          home_currency: homeCurrency,
        });
        setSessionId(res.session_id || sessionId);
        setResult(res);
        pushHistoryRow(mode === "camera" ? "Camera photo" : "QR image", res);
      }
    } catch (e) {
      const msg = e?.message || "Failed to translate";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function onClearHistory() {
    setError("");
    try {
      await clearHistory({ apiKey: apiKeyInput, user_id: USER_ID, session_id: sessionId });
      setHistory([]);
      setResult(null);
    } catch (e) {
      setError(e?.message || "Failed to clear history");
    }
  }

  return (
    <div className="page">
      <div className="container">
        <h1 className="title">Travel QR Cost Estimator</h1>
        <p className="subtitle">
          Estimate costs from supported QRs, explore fees, and check cash payments in a supported local currency. No payments are made here.
        </p>

        <div className="tabs" role="group" aria-label="Workspace">
          <button type="button" className={`tab ${workspace === "demo" ? "active" : ""}`} disabled={loading} onClick={() => setWorkspace("demo")}>QR demo</button>
          <button type="button" className={`tab ${workspace === "account" ? "active" : ""}`} disabled={loading} onClick={() => setWorkspace("account")}>Saved scans</button>
          <button type="button" className={`tab ${workspace === "converter" ? "active" : ""}`} disabled={loading} onClick={() => setWorkspace("converter")}>Currency converter</button>
          <button type="button" className={`tab ${workspace === "cash" ? "active" : ""}`} disabled={loading} onClick={() => setWorkspace("cash")}>Cash helper</button>
        </div>
        {workspace === "cash" ? <CashHelper /> : workspace === "account" ? <AccountPanel />
          : workspace === "converter" ? <CurrencyConverter apiKey={apiKeyInput} onApiKeyChange={setApiKeyInput} /> : <>
        <div className="card">
          <label className="label" htmlFor="api-key">Local demo API key (required)</label>
          <input id="api-key" className="textarea" type="password" autoComplete="off" disabled={loading} value={apiKeyInput} onChange={(e) => { setApiKeyInput(e.target.value); setResult(null); }} placeholder="Enter QR_API_KEY from your backend environment" />
          <p className="hint">Demo key held in this page only; not saved to browser storage. Use synthetic QR payloads, never real payment data.</p>
          <HomeCurrency value={homeCurrency} disabled={loading} onChange={value => {
            setHomeCurrency(value); setResult(null); setError("");
          }} />
          <div className="tabs">
            <button
              className={`tab ${mode === "text" ? "active" : ""}`}
              disabled={loading} onClick={() => changeMode("text")}
            >
              Text
            </button>
            <button
              className={`tab ${mode === "image" ? "active" : ""}`}
              disabled={loading} onClick={() => changeMode("image")}
            >
              Image
            </button>
            <button className={`tab ${mode === "camera" ? "active" : ""}`} disabled={loading}
              onClick={() => changeMode("camera")}>Camera</button>
          </div>

          {mode === "text" ? (
            <div className="form">
              <label className="label" htmlFor="qr-text">QR Text</label>
              <textarea
                className="textarea" id="qr-text" disabled={loading}
                value={qrText}
                onChange={(e) => { setQrText(e.target.value); setResult(null); setError(""); }}
                rows={3}
                placeholder="QR:JP:JPY:1500"
              />
              <div className="hint">Tip: You can paste multiple: QR:JP:JPY:1500,QR:US:USD:12</div>
            </div>
          ) : (
            <QRPhoto key={mode} camera={mode === "camera"} file={imageFile} disabled={loading}
              onChange={file => { setImageFile(file); setResult(null); setError(""); }} />
          )}

          <div className="actions">
            <button className="btnPrimary" onClick={onTranslate} disabled={loading}>
              {loading ? "Estimating..." : "Estimate cost"}
            </button>

            <button className="btnSecondary" onClick={onClearHistory} disabled={loading}>
              Clear History
            </button>
          </div>

          {error ? <div className="error">{error}</div> : null}
        </div>

        <div className="card">
          <h2 className="sectionTitle">Result</h2>
          {!result && <p className="hintText">Scan a QR to see its reference conversion.</p>}

          <div className="resultRow">
            <div className="total">Reference estimate (before fees): <span className="money">{formatMoney(totalINR, resultCurrency)}</span></div>
          </div>

          <ScanInsights result={result} />
        </div>

        <div className="card">
          <div className="historyHeader">
            <h2 className="sectionTitle">History</h2>
          </div>

          <div className="tableWrap">
            <table className="table demoHistory">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Input</th>
                  <th>Reference total</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="empty">No history yet.</td>
                  </tr>
                ) : (
                  history.map((r, idx) => (
                    <tr key={idx}>
                      <td className="mono">{r.time}</td>
                      <td className="mono">{r.input}</td>
                      <td className="mono">{formatMoney(r.total, r.currency)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
        </>}
      </div>
    </div>
  );
}

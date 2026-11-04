import { useRef, useState } from "react";
import { scanImage, scanText } from "../lib/api";
import { isDemoPayload } from "../lib/qrFormats";
import { formatMoney } from "../lib/money";
import HomeCurrency from "./HomeCurrency";
import QRPhoto from "./QRPhoto";
import ScanInsights from "./ScanInsights";

const INPUT_MODES = [["text", "Text"], ["image", "Image"], ["camera", "Camera"]];

function totalOf(result) {
  if (!result) return null;
  return result.multiple ? result.total_home : result.fx_result?.total_home ?? null;
}

function currencyOf(result) {
  return result?.home_currency || result?.fx_result?.to_currency || "INR";
}

export default function QRDemo({ apiKey, onApiKeyChange, publicDemo }) {
  const [mode, setMode] = useState("text");
  const [qrText, setQrText] = useState("QR:JP:JPY:1500");
  const [imageFile, setImageFile] = useState(null);
  const [homeCurrency, setHomeCurrency] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const nextRowId = useRef(1);

  function resetResult() {
    setResult(null);
    setError("");
  }

  function changeMode(next) {
    setMode(next);
    setImageFile(null);
    resetResult();
  }

  function keyProblem() {
    if (apiKey.trim()) return "";
    if (mode !== "text") return "Image and camera scans need the private demo API key.";
    if (!publicDemo) return "Enter the demo API key to estimate.";
    if (!isDemoPayload(qrText)) {
      return "Without a key, only synthetic demo strings such as QR:JP:JPY:1500 are accepted. UPI and EMV payloads need the private demo API key.";
    }
    return "";
  }

  async function estimate() {
    resetResult();
    const payload = qrText.trim();
    if (mode === "text" && !payload) { setError("Please enter QR text."); return; }
    if (mode !== "text" && !imageFile) { setError("Please choose a QR image file."); return; }
    const problem = keyProblem();
    if (problem) { setError(problem); return; }
    setLoading(true);
    try {
      const response = mode === "text"
        ? await scanText({ apiKey, qr_payload: payload, home_currency: homeCurrency })
        : await scanImage({ apiKey, file: imageFile, home_currency: homeCurrency });
      setResult(response);
      const label = mode === "text" ? "Text QR (hidden)" : mode === "camera" ? "Camera photo" : "QR image";
      setHistory(rows => [{
        id: nextRowId.current++, time: new Date().toLocaleTimeString(), input: label,
        total: totalOf(response), currency: currencyOf(response),
      }, ...rows]);
    } catch (problem) {
      setError(problem.message || "Estimate failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function clearHistory() {
    // This history lives only in the page, so clearing it needs no server call.
    setHistory([]);
    resetResult();
  }

  return <>
    <div className="card">
      <label className="label" htmlFor="api-key">Demo API key {publicDemo ? "(optional for QR: demo strings)" : "(required)"}</label>
      <input id="api-key" className="textarea" type="password" autoComplete="off" disabled={loading} value={apiKey}
        onChange={e => { onApiKeyChange(e.target.value); setResult(null); }}
        placeholder={publicDemo ? "Leave empty to try the synthetic demo strings" : "Enter QR_API_KEY from your backend environment"} />
      <p className="hint">Key held in this page only; not saved to browser storage. Use synthetic QR payloads, never real payment data.</p>
      <HomeCurrency value={homeCurrency} disabled={loading} onChange={value => { setHomeCurrency(value); resetResult(); }} />
      <div className="tabs" role="group" aria-label="QR input">
        {INPUT_MODES.map(([value, label]) => <button key={value} type="button" disabled={loading}
          className={`tab ${mode === value ? "active" : ""}`} onClick={() => changeMode(value)}>{label}</button>)}
      </div>
      {mode === "text" ? <div className="form">
        <label className="label" htmlFor="qr-text">QR Text</label>
        <textarea className="textarea" id="qr-text" disabled={loading} rows={3} value={qrText}
          placeholder="QR:JP:JPY:1500" onChange={e => { setQrText(e.target.value); resetResult(); }} />
        <div className="hint">Tip: paste several at once, e.g. QR:JP:JPY:1500,QR:US:USD:12</div>
      </div> : <QRPhoto key={mode} camera={mode === "camera"} file={imageFile} disabled={loading}
        onChange={file => { setImageFile(file); resetResult(); }} />}
      <div className="actions">
        <button className="btnPrimary" type="button" onClick={estimate} disabled={loading}>
          {loading ? "Estimating..." : "Estimate cost"}
        </button>
        <button className="btnSecondary" type="button" onClick={clearHistory} disabled={loading}>Clear History</button>
      </div>
      {error ? <div className="error" role="alert">{error}</div> : null}
    </div>

    <div className="card">
      <h2 className="sectionTitle">Result</h2>
      {!result && <p className="hintText">Scan a QR to see its reference conversion.</p>}
      <div className="resultRow">
        <div className="total">Reference estimate (before fees): <span className="money">{result ? formatMoney(totalOf(result), currencyOf(result)) : "—"}</span></div>
      </div>
      <ScanInsights result={result} />
    </div>

    <div className="card">
      <div className="historyHeader"><h2 className="sectionTitle">History</h2></div>
      <div className="tableWrap">
        <table className="table demoHistory">
          <thead><tr><th>Time</th><th>Input</th><th>Reference total</th></tr></thead>
          <tbody>
            {history.length === 0
              ? <tr><td colSpan="3" className="empty">No history yet.</td></tr>
              : history.map(row => <tr key={row.id}>
                <td className="mono">{row.time}</td>
                <td className="mono">{row.input}</td>
                <td className="mono">{formatMoney(row.total, row.currency)}</td>
              </tr>)}
          </tbody>
        </table>
      </div>
    </div>
  </>;
}

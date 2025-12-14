import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { scanImage, scanText, clearHistory } from "./lib/api";

const USER_ID = "user-123";

function formatINR(x) {
  const n = Number(x);
  if (Number.isNaN(n)) return "₹0.00";
  return `₹${n.toFixed(2)}`;
}

function extractTotalINR(result) {
  if (!result) return 0;

  // multi
  if (result.multiple && typeof result.total_home === "number") return result.total_home;

  // single
  const fx = result.fx_result;
  if (fx && typeof fx.total_home === "number") return fx.total_home;

  return 0;
}

function extractRisk(result) {
  if (!result) return "unknown";

  if (result.multiple && Array.isArray(result.items)) {
    const levels = result.items
      .map((x) => x?.risk_result?.risk_level)
      .filter(Boolean);

    if (!levels.length) return "unknown";

    // if different, say mixed
    const uniq = new Set(levels);
    if (uniq.size > 1) return "mixed";
    return levels[0];
  }

  return result?.risk_result?.risk_level || "unknown";
}

function extractNote(result) {
  if (!result) return "";
  return result.message || result.error || "";
}

export default function App() {
  const [mode, setMode] = useState("text"); // "text" | "image"
  const [qrText, setQrText] = useState("QR:JP:JPY:1500");
  const [imageFile, setImageFile] = useState(null);

  const [sessionId, setSessionId] = useState(""); // backend will return real session id
  const [userCountry, setUserCountry] = useState("");

  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Detect region from browser language (free + stable)
  useEffect(() => {
    const lang = navigator.language || "";
    const parts = lang.split("-");
    if (parts.length === 2) setUserCountry(parts[1].toUpperCase());
  }, []);

  const totalINR = useMemo(() => extractTotalINR(result), [result]);
  const risk = useMemo(() => extractRisk(result), [result]);
  const note = useMemo(() => extractNote(result), [result]);

  function pushHistoryRow(inputLabel, resObj) {
    const t = new Date();
    const time = t.toLocaleTimeString();

    const row = {
      time,
      input: inputLabel,
      total: extractTotalINR(resObj),
      risk: extractRisk(resObj),
      note: extractNote(resObj),
      raw: resObj,
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
          user_id: USER_ID,
          session_id: sessionId,
          qr_payload: payload,
          user_country: userCountry,
        });
        setSessionId(res.session_id || sessionId);
        setResult(res);
        pushHistoryRow(payload, res);
      } else {
        if (!imageFile) throw new Error("Please choose a QR image file.");
        res = await scanImage({
          user_id: USER_ID,
          session_id: sessionId,
          file: imageFile,
          user_country: userCountry,
        });
        setSessionId(res.session_id || sessionId);
        setResult(res);
        pushHistoryRow(imageFile.name, res);
      }
    } catch (e) {
      const msg = e?.message || "Failed to translate";
      setError(msg);
      const fake = { error: msg, message: msg };
      setResult(fake);
      pushHistoryRow(mode === "text" ? (qrText || "text") : (imageFile?.name || "image"), fake);
    } finally {
      setLoading(false);
    }
  }

  async function onClearHistory() {
    setError("");
    try {
      await clearHistory({ user_id: USER_ID, session_id: sessionId });
      setHistory([]);
      setResult(null);
    } catch (e) {
      setError(e?.message || "Failed to clear history");
    }
  }

  return (
    <div className="page">
      <div className="container">
        <h1 className="title">Universal QR Payment Translator</h1>
        <p className="subtitle">
          Paste QR text or upload a QR image. Get FX + fees + risk in INR.
          <span className="region">Detected region: <b>{userCountry || "Unknown"}</b></span>
        </p>

        <div className="card">
          <div className="tabs">
            <button
              className={`tab ${mode === "text" ? "active" : ""}`}
              onClick={() => setMode("text")}
            >
              Text
            </button>
            <button
              className={`tab ${mode === "image" ? "active" : ""}`}
              onClick={() => setMode("image")}
            >
              Image
            </button>
          </div>

          {mode === "text" ? (
            <div className="form">
              <label className="label">QR Text</label>
              <textarea
                className="textarea"
                value={qrText}
                onChange={(e) => setQrText(e.target.value)}
                rows={3}
                placeholder="QR:JP:JPY:1500"
              />
              <div className="hint">Tip: You can paste multiple: QR:JP:JPY:1500,QR:US:USD:12</div>
            </div>
          ) : (
            <div className="form">
              <label className="label">QR Image</label>
              <input
                className="file"
                type="file"
                accept="image/*"
                onChange={(e) => setImageFile(e.target.files?.[0] || null)}
              />
              <div className="hint">Selected: {imageFile ? imageFile.name : "none"}</div>
            </div>
          )}

          <div className="actions">
            <button className="btnPrimary" onClick={onTranslate} disabled={loading}>
              {loading ? "Translating..." : "Translate"}
            </button>

            <button className="btnSecondary" onClick={onClearHistory} disabled={loading}>
              Clear History
            </button>
          </div>

          {error ? <div className="error">{error}</div> : null}
        </div>

        <div className="card">
          <h2 className="sectionTitle">Result</h2>
          <div className="resultText">{note || "No result yet."}</div>

          <div className="resultRow">
            <div className="total">Total: <span className="money">{formatINR(totalINR)}</span></div>
            <span className={`pill ${risk}`}>{risk}</span>
          </div>

          <details className="raw">
            <summary>Show Raw JSON</summary>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>

        <div className="card">
          <div className="historyHeader">
            <h2 className="sectionTitle">History</h2>
          </div>

          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Input</th>
                  <th>Total (INR)</th>
                  <th>Risk</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty">No history yet.</td>
                  </tr>
                ) : (
                  history.map((r, idx) => (
                    <tr key={idx}>
                      <td className="mono">{r.time}</td>
                      <td className="mono">{r.input}</td>
                      <td className="mono">{formatINR(r.total).replace("₹", "₹")}</td>
                      <td><span className={`pill ${r.risk}`}>{r.risk}</span></td>
                      <td className="noteCell">
                        <details>
                          <summary>View</summary>
                          <div className="noteFull">{r.note}</div>
                          <pre className="noteJson">{JSON.stringify(r.raw, null, 2)}</pre>
                        </details>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}

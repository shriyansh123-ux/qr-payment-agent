import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { getHistory, scanImage, scanText } from "./lib/api";

function formatINR(x) {
  const n = Number(x);
  if (!Number.isFinite(n)) return "₹0.00";
  return `₹${n.toFixed(2)}`;
}

function riskPillClass(risk) {
  const r = (risk || "unknown").toLowerCase();
  if (r === "low") return "pill pill-low";
  if (r === "medium") return "pill pill-med";
  if (r === "high") return "pill pill-high";
  if (r === "error") return "pill pill-err";
  return "pill pill-unk";
}

function NoteCell({ text }) {
  const [open, setOpen] = useState(false);
  if (!text) return <span className="muted">—</span>;

  // keep it "compressed" but not trimmed forever
  const short = text.length > 120 ? text.slice(0, 120) + "…" : text;

  return (
    <div className="noteCell">
      <div className="noteText">{open ? text : short}</div>
      {text.length > 120 && (
        <button className="linkBtn" onClick={() => setOpen(!open)}>
          {open ? "Show less" : "Show more"}
        </button>
      )}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("text"); // "text" | "image"
  const [qrText, setQrText] = useState("QR:JP:JPY:1500");
  const [file, setFile] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [raw, setRaw] = useState(null);

  // summary comes from server (we added it)
  const [summary, setSummary] = useState({
    total_home: 0,
    home_currency: "INR",
    risk_level: "unknown",
    note: "",
  });

  const [history, setHistory] = useState([]);

  async function refreshHistory() {
    const data = await getHistory({ userId: "user-123", limit: 50 });
    setHistory(data.items || []);
  }

  useEffect(() => {
    refreshHistory().catch(() => {});
  }, []);

  const resultMessage = useMemo(() => {
    // Prefer orchestrator message, fallback to summary.note
    const msg =
      raw?.result?.message ||
      raw?.result?.message?.toString?.() ||
      summary.note ||
      "";
    return msg;
  }, [raw, summary.note]);

  async function onTranslate() {
    setError("");
    setLoading(true);
    setRaw(null);
    setSummary({
      total_home: 0,
      home_currency: "INR",
      risk_level: "unknown",
      note: "",
    });

    try {
      let data;
      if (tab === "text") {
        const payload = (qrText || "").trim();
        if (!payload) throw new Error("Please enter QR text.");
        data = await scanText({ userId: "user-123", sessionId: "", qrPayload: payload });
      } else {
        if (!file) throw new Error("Please choose a QR image.");
        data = await scanImage({ userId: "user-123", sessionId: "", file });
      }

      // data = { result: {...}, summary: {...} }
      setRaw(data);
      setSummary(data.summary || summary);

      // refresh table from SQLite (single source of truth)
      await refreshHistory();
    } catch (e) {
      setError(e?.message || "Failed to fetch");
      // show it in result panel too
      setSummary({
        total_home: 0,
        home_currency: "INR",
        risk_level: "error",
        note: e?.message || "Failed to fetch",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Universal QR Payment Translator</h1>
        <p className="sub">Paste QR text or upload a QR image. Get FX + fees + risk in INR.</p>
      </header>

      <div className="card">
        <div className="tabs">
          <button className={tab === "text" ? "tab active" : "tab"} onClick={() => setTab("text")}>
            Text
          </button>
          <button className={tab === "image" ? "tab active" : "tab"} onClick={() => setTab("image")}>
            Image
          </button>
        </div>

        {tab === "text" ? (
          <div className="form">
            <label className="label">QR Text</label>
            <textarea
              value={qrText}
              onChange={(e) => setQrText(e.target.value)}
              className="input"
              rows={3}
              placeholder="QR:JP:JPY:1500"
            />
            <div className="row">
              <button className="btn" onClick={onTranslate} disabled={loading}>
                {loading ? "Translating..." : "Translate"}
              </button>
            </div>
          </div>
        ) : (
          <div className="form">
            <label className="label">QR Image</label>
            <input
              type="file"
              accept="image/*"
              className="file"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file && <div className="muted">Selected: {file.name}</div>}
            <div className="row">
              <button className="btn" onClick={onTranslate} disabled={loading}>
                {loading ? "Translating..." : "Translate"}
              </button>
            </div>
          </div>
        )}

        {error && <div className="error">{error}</div>}
      </div>

      <div className="card">
        <h2>Result</h2>

        <div className="resultText">
          {resultMessage ? <NoteCell text={resultMessage} /> : <span className="muted">No result yet.</span>}
        </div>

        <div className="resultMeta">
          <div className="total">
            <span>Total:</span>
            <strong>{formatINR(summary.total_home)}</strong>
            <span className={riskPillClass(summary.risk_level)}>{summary.risk_level || "unknown"}</span>
          </div>
        </div>

        <details className="jsonBox">
          <summary>Show Raw JSON</summary>
          <pre>{JSON.stringify(raw, null, 2)}</pre>
        </details>
      </div>

      <div className="card">
        <h2>History</h2>

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
                  <td colSpan={5} className="muted">
                    No history yet.
                  </td>
                </tr>
              ) : (
                history.map((h) => (
                  <tr key={h.id}>
                    <td className="mono">{h.created_at}</td>
                    <td className="mono">{h.input_repr}</td>
                    <td className="mono">{formatINR(h.total_home)}</td>
                    <td>
                      <span className={riskPillClass(h.risk_level)}>{h.risk_level}</span>
                    </td>
                    <td>
                      <NoteCell text={h.note} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

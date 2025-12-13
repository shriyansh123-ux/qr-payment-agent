import { useState } from "react";
import { scanText, scanImage } from "../api/client";

export default function QRForm({ onResult }) {
  const [mode, setMode] = useState("text");
  const [qrText, setQrText] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit() {
    setError("");
    setLoading(true);

    try {
      let res;

      if (mode === "text") {
        res = await scanText(qrText);
        onResult(res, qrText);
      } else {
        if (!file) throw new Error("No image selected");
        res = await scanImage(file);
        onResult(res, file.name);
      }

      if (!res.success) setError(res.error?.message || "Failed");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="toggle">
        <button onClick={() => setMode("text")}>Text</button>
        <button onClick={() => setMode("image")}>Image</button>
      </div>

      {mode === "text" ? (
        <textarea
          placeholder="QR:JP:JPY:1500,QR:US:USD:12"
          value={qrText}
          onChange={(e) => setQrText(e.target.value)}
        />
      ) : (
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
      )}

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Processing..." : "Translate"}
      </button>

      {error && <p className="error">{error}</p>}
    </div>
  );
}

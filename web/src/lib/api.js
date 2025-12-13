// web/src/lib/api.js

// If VITE_API_BASE is not set, fallback to local FastAPI
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function reqId() {
  // simple request id for tracing logs
  return crypto?.randomUUID ? crypto.randomUUID() : String(Date.now());
}

export async function scanText({ userId = "user-123", sessionId = "", qrPayload }) {
  const r = await fetch(`${API_BASE}/api/scan-text`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-Id": reqId(),
    },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      qr_payload: qrPayload,
    }),
  });

  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
  return data;
}

export async function scanImage({ userId = "user-123", sessionId = "", file }) {
  const fd = new FormData();
  fd.append("file", file);

  const r = await fetch(
    `${API_BASE}/api/scan-image?user_id=${encodeURIComponent(userId)}&session_id=${encodeURIComponent(sessionId)}`,
    {
      method: "POST",
      headers: {
        "X-Request-Id": reqId(),
      },
      body: fd,
    }
  );

  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
  return data;
}

export async function getHistory({ userId = "user-123", limit = 50 }) {
  const r = await fetch(
    `${API_BASE}/api/history?user_id=${encodeURIComponent(userId)}&limit=${limit}`,
    { headers: { "X-Request-Id": reqId() } }
  );
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data?.error || `HTTP ${r.status}`);
  return data;
}

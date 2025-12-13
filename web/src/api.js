const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function scanText({ user_id, session_id, qr_payload }) {
  const res = await fetch(`${API_BASE}/api/scan-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, session_id, qr_payload }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || data?.error || `HTTP ${res.status}`);
  return data;
}

export async function scanImage({ user_id, session_id, file }) {
  const fd = new FormData();
  fd.append("file", file);                 // IMPORTANT: field name must be "file"
  fd.append("session_id", session_id || ""); // optional

  const res = await fetch(`${API_BASE}/api/scan-image?user_id=${encodeURIComponent(user_id)}`, {
    method: "POST",
    body: fd,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.detail || data?.error || `HTTP ${res.status}`);
  return data;
}

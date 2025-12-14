const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function scanText({ user_id, session_id, qr_payload, user_country }) {
  const res = await fetch(`${API_BASE}/api/scan-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id,
      session_id,
      qr_payload,
      user_country: user_country || null,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to scan text");
  }
  return res.json();
}

export async function scanImage({ user_id, session_id, file, user_country }) {
  const fd = new FormData();
  fd.append("file", file);

  const url =
    `${API_BASE}/api/scan-image?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}` +
    `&user_country=${encodeURIComponent(user_country || "")}`;

  const res = await fetch(url, { method: "POST", body: fd });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to scan image");
  }
  return res.json();
}

export async function getHistory({ user_id, session_id }) {
  const url =
    `${API_BASE}/api/history?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function clearHistory({ user_id, session_id }) {
  const url =
    `${API_BASE}/api/clear-history?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json();
}

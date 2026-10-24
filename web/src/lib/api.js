// Development-only shared key, entered by the user; not bundled at build time.
// Secrets remain in React state for this tab, not browser session/local storage.
// Same-origin API in production; Vite proxies /api to FastAPI during local development.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function scanText({ apiKey, user_id, session_id, qr_payload, user_country }) {
  const res = await fetch(`${API_BASE}/api/scan-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
    body: JSON.stringify({
      user_id,
      session_id,
      qr_payload,
      user_country: /^[A-Z]{2}$/.test(user_country || "") ? user_country : null,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to scan text");
  }
  return res.json();
}

export async function scanImage({ apiKey, user_id, session_id, file, user_country }) {
  const fd = new FormData();
  fd.append("file", file);

  const url =
    `${API_BASE}/api/scan-image?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}` +
    `&user_country=${encodeURIComponent(/^[A-Z]{2}$/.test(user_country || "") ? user_country : "")}`;

  const res = await fetch(url, { method: "POST", headers: { "X-API-Key": apiKey }, body: fd });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to scan image");
  }
  return res.json();
}

export async function getHistory({ apiKey, user_id, session_id }) {
  const url =
    `${API_BASE}/api/history?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}`;
  const res = await fetch(url, { headers: { "X-API-Key": apiKey } });
  if (!res.ok) throw new Error("Failed to fetch history");
  return res.json();
}

export async function clearHistory({ apiKey, user_id, session_id }) {
  const url =
    `${API_BASE}/api/clear-history?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}`;
  const res = await fetch(url, { method: "POST", headers: { "X-API-Key": apiKey } });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json();
}

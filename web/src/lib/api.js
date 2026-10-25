// Development-only shared key, entered by the user; not bundled at build time.
// Secrets remain in React state for this tab, not browser session/local storage.
// Same-origin API in production; Vite proxies /api to FastAPI during local development.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function scanText({ apiKey, user_id, session_id, qr_payload, user_country, home_currency }) {
  const res = await fetch(`${API_BASE}/api/scan-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
    body: JSON.stringify({
      user_id,
      session_id,
      qr_payload,
      home_currency: home_currency || null,
      user_country: /^[A-Z]{2}$/.test(user_country || "") ? user_country : null,
    }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || "Failed to scan text");
  }
  return res.json();
}

export async function scanImage({ apiKey, user_id, session_id, file, user_country, home_currency }) {
  const fd = new FormData();
  fd.append("file", file);

  const url =
    `${API_BASE}/api/scan-image?user_id=${encodeURIComponent(user_id)}` +
    `&session_id=${encodeURIComponent(session_id || "")}` +
    `&user_country=${encodeURIComponent(/^[A-Z]{2}$/.test(user_country || "") ? user_country : "")}` +
    (home_currency ? `&home_currency=${encodeURIComponent(home_currency)}` : "");

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


// Optional database-backed account workspace. Tokens remain only in React state.
async function accountRequest(path, { method = "GET", token = "", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/account${path}`, {
    method, headers, ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  let data;
  try { data = await res.json(); } catch { data = {}; }
  if (!res.ok) {
    const message = typeof data?.detail === "string" ? data.detail : "Account request failed";
    const error = new Error(message);
    error.status = res.status;
    throw error;
  }
  return data;
}

export const accountStatus = () => accountRequest("/status");

export async function getCurrencies() {
  const response = await fetch(`${API_BASE}/api/currencies`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Currency list unavailable.");
  return data;
}

export async function convertCurrency({ apiKey, ...body }) {
  const response = await fetch(`${API_BASE}/api/convert`, {
    method: "POST", headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check the amount and selected currencies.");
  return data;
}
export const accountRegister = (email, password) =>
  accountRequest("/register", { method: "POST", body: { email, password } });
export const accountLogin = (email, password) =>
  accountRequest("/login", { method: "POST", body: { email, password } });
export const accountLogout = (token) =>
  accountRequest("/logout", { method: "POST", token });
export const accountMe = (token) => accountRequest("/me", { token });
export const accountHistory = (token) => accountRequest("/history", { token });
export const accountClearHistory = (token) =>
  accountRequest("/clear-history", { method: "POST", token });
export const accountScanText = (token, qr_payload, user_country, home_currency) =>
  accountRequest("/scan-text", {
    method: "POST", token,
    body: { qr_payload, home_currency: home_currency || null, user_country: /^[A-Z]{2}$/.test(user_country || "") ? user_country : null },
  });

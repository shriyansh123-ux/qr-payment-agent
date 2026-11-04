// Same-origin API in production; Vite proxies /api to FastAPI during development.
// Keys and tokens are passed in from React state and never written to browser storage.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// FastAPI returns `detail` as a string, or as a list of validation problems for 422s.
function describe(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map(item => item?.msg).filter(Boolean);
    if (messages.length) return messages.join("; ");
  }
  return null;
}

function fallbackMessage(status) {
  if (status === 429) return "Too many requests. Wait a minute and try again.";
  if (status >= 500) return "The service is unavailable right now. The free server may be waking up; try again in a minute.";
  return `Request failed (HTTP ${status}).`;
}

async function request(path, { method = "GET", apiKey = "", token = "", json, body } = {}) {
  const headers = {};
  if (json !== undefined) headers["Content-Type"] = "application/json";
  if (apiKey) headers["X-API-Key"] = apiKey;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method, headers, body: json !== undefined ? JSON.stringify(json) : body,
    });
  } catch {
    throw new ApiError("Could not reach the server. Check your connection and try again.", 0);
  }
  let data = null;
  try { data = await response.json(); } catch { /* e.g. an HTML error page during a cold start */ }
  if (!response.ok) {
    throw new ApiError(describe(data?.detail) || fallbackMessage(response.status), response.status);
  }
  if (data === null) throw new ApiError("The server sent an unexpected response.", response.status);
  return data;
}

export const getConfig = () => request("/api/config");
export const getCurrencies = () => request("/api/currencies");

export const scanText = ({ apiKey, qr_payload, home_currency }) =>
  request("/api/scan-text", { method: "POST", apiKey, json: { qr_payload, home_currency: home_currency || null } });

export function scanImage({ apiKey, file, home_currency }) {
  const form = new FormData();
  form.append("file", file);
  const query = home_currency ? `?home_currency=${encodeURIComponent(home_currency)}` : "";
  return request(`/api/scan-image${query}`, { method: "POST", apiKey, body: form });
}

export const convertCurrency = ({ apiKey, ...json }) =>
  request("/api/convert", { method: "POST", apiKey, json });

// Optional database-backed account workspace.
export const accountStatus = () => request("/api/account/status");
export const accountRegister = (email, password) =>
  request("/api/account/register", { method: "POST", json: { email, password } });
export const accountLogin = (email, password) =>
  request("/api/account/login", { method: "POST", json: { email, password } });
export const accountLogout = token => request("/api/account/logout", { method: "POST", token });
export const accountHistory = token => request("/api/account/history", { token });
export const accountClearHistory = token => request("/api/account/clear-history", { method: "POST", token });
export const accountScanText = (token, qr_payload, home_currency) =>
  request("/api/account/scan-text", { method: "POST", token, json: { qr_payload, home_currency: home_currency || null } });

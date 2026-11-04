// Mirrors is_demo_payload() in src/parsers/qr_text.py.
const DEMO_QR = /^QR:[A-Z]{2}:[A-Z]{3}:[0-9]+(?:\.[0-9]{1,2})?$/i;
export function isDemoPayload(text) {
  const value = (text || "").trim();
  if (!value.toUpperCase().startsWith("QR:")) return false;
  const parts = value.split(/[,\n]+/).map(part => part.trim()).filter(Boolean);
  return parts.length > 0 && parts.length <= 10 && parts.every(part => DEMO_QR.test(part));
}

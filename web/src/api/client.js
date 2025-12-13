const API_BASE = "http://127.0.0.1:8000/api";

export async function scanText(qrPayload) {
  const res = await fetch(`${API_BASE}/scan-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "react-user",
      session_id: "",
      qr_payload: qrPayload,
    }),
  });
  return res.json();
}

export async function scanImage(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(
    `${API_BASE}/scan-image?user_id=react-user`,
    {
      method: "POST",
      body: form,
    }
  );
  return res.json();
}

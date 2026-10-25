import { useId, useState } from "react";

// Native photo capture avoids continuously streaming the camera or requesting audio.
export default function QRPhoto({ file, onChange, disabled, camera = false }) {
  const id = useId();
  const [error, setError] = useState("");
  return <div className="form">
    <label className="label" htmlFor={id}>{camera ? "Take QR photo" : "QR image"}</label>
    <input id={id} className="file" type="file" accept="image/png,image/jpeg,image/webp"
      {...(camera ? { capture: "environment" } : {})} disabled={disabled}
      onChange={event => {
        const selected = event.target.files?.[0] || null;
        setError("");
        if (selected && (!['image/png', 'image/jpeg', 'image/webp'].includes(selected.type) || selected.size > 3 * 1024 * 1024)) {
          setError("Choose a PNG, JPEG or WebP photo no larger than 3 MiB. Use a lower photo resolution if needed.");
          onChange(null); event.target.value = ""; return;
        }
        onChange(selected);
      }} />
    <p className="hint">{camera
      ? "On supported phones this opens the rear camera; other browsers may show a file picker. Capture one clear QR, then select Estimate cost. Only the selected photo is uploaded."
      : "PNG, JPEG or WebP, up to 3 MiB. Use one clearly visible QR."}</p>
    <p className="hint">Selected: {file ? file.name : "none"}</p>
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

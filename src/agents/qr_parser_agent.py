class QRParserAgent:
    def parse_single(self, payload: str):
        parts = payload.split(":")
        return {
            "merchant_id": "M12345",
            "country": parts[1],
            "currency": parts[2],
            "amount": float(parts[3]),
            "raw": payload
        }

    def handle(self, qr_payload: str):
        qr_payload = qr_payload.strip()

        # Split multi-QR input
        candidates = [
            p.strip() for p in qr_payload.replace("\n", ",")
                                         .replace(" ", ",")
                                         .split(",")
            if p.strip()
        ]

        if len(candidates) == 1:
            return self.parse_single(candidates[0])
        
        # MULTI-QR mode
        output = []
        for c in candidates:
            try:
                output.append(self.parse_single(c))
            except Exception:
                continue

        return {
            "multiple": True,
            "count": len(output),
            "items": output
        }

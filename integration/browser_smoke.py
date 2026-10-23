"""Real Chromium smoke test of the React frontend and FastAPI backend."""
import os
import tempfile
from pathlib import Path

import qrcode
from playwright.sync_api import sync_playwright, expect

PAYLOAD = "upi://pay?pa=merchant@upi&am=100&cu=INR"
KEY = os.environ["QR_API_KEY"]


def run():
    with tempfile.TemporaryDirectory() as folder:
        qr_image = Path(folder) / "qr.png"
        qrcode.make(PAYLOAD).save(qr_image)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded")
                expect(page.get_by_role("heading", name="Universal QR Payment Translator")).to_be_visible()

                page.locator("#api-key").fill(KEY)
                page.locator("textarea").fill(PAYLOAD)
                with page.expect_response(lambda r: "/api/scan-text" in r.url and r.request.method == "POST") as scan_response:
                    page.get_by_role("button", name="Translate", exact=True).click()
                scan = scan_response.value
                assert scan.ok, f"Browser-to-API text scan failed: status={scan.status}, error={scan.text()[:300]}"
                expect(page.locator(".money")).to_have_text("₹100.00", timeout=10000)
                expect(page.locator(".noteCell")).to_have_count(1)

                page.get_by_role("button", name="Image", exact=True).click()
                page.locator("input[type=file]").set_input_files(str(qr_image))
                page.get_by_role("button", name="Translate", exact=True).click()
                expect(page.locator(".money")).to_have_text("₹100.00", timeout=30000)
                expect(page.locator(".noteCell")).to_have_count(2)

                page.get_by_role("button", name="Clear History").click()
                expect(page.get_by_text("No history yet.")).to_be_visible()
                print("Browser E2E passed: authenticated text scan, image scan, result, history, clear")
            finally:
                browser.close()


if __name__ == "__main__":
    run()

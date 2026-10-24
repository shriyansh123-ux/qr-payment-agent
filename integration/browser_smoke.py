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
                page.goto(os.getenv("QR_BROWSER_URL", "http://127.0.0.1:5173"), wait_until="domcontentloaded")
                expect(page.get_by_role("heading", name="Universal QR Payment Translator")).to_be_visible()

                page.locator("#api-key").fill(KEY)
                page.locator("textarea").fill(PAYLOAD)
                with page.expect_response(lambda r: "/api/scan-text" in r.url and r.request.method == "POST") as scan_response:
                    page.get_by_role("button", name="Translate", exact=True).click()
                scan = scan_response.value
                assert scan.ok, f"Browser-to-API text scan failed: status={scan.status}, error={scan.text()[:300]}"
                expect(page.locator(".money")).to_have_text("₹100.00", timeout=10000)
                expect(page.locator(".noteCell")).to_have_count(1)
                expect(page.get_by_text("Text QR (hidden)")).to_be_visible()
                assert PAYLOAD not in page.locator("tbody").inner_text()
                assert page.evaluate("sessionStorage.getItem(\'qr_demo_api_key\')") is None

                page.get_by_role("button", name="Image", exact=True).click()
                page.locator("input[type=file]").set_input_files(str(qr_image))
                page.get_by_role("button", name="Translate", exact=True).click()
                expect(page.locator(".money")).to_have_text("₹100.00", timeout=30000)
                expect(page.locator(".noteCell")).to_have_count(2)

                page.get_by_role("button", name="Clear History").click()
                expect(page.get_by_text("No history yet.")).to_be_visible()
                # Optional account flows run only against a locally configured SQLite DB.
                page.get_by_role("button", name="Accounts", exact=True).click()
                expect(page.get_by_role("heading", name="Account workspace")).to_be_visible()
                page.get_by_role("button", name="Create test account").click()
                page.locator("#account-email").fill("synthetic.browser@example.invalid")
                page.locator("#account-password").fill("synthetic-example-password-1234")
                page.get_by_role("button", name="Register", exact=True).click()
                expect(page.get_by_text("Test account created. Sign in to continue.")).to_be_visible()
                page.locator("#account-password").fill("synthetic-example-password-1234")
                page.get_by_role("button", name="Sign in", exact=True).last.click()
                expect(page.get_by_text("Signed in:")).to_be_visible()
                page.locator("#account-qr").fill(PAYLOAD)
                page.get_by_role("button", name="Translate and save summary").click()
                expect(page.get_by_text("Stored summary history")).to_be_visible()
                expect(page.locator(".accountTable tbody tr")).to_have_count(1, timeout=15000)
                assert "merchant@upi" not in page.locator(".accountTable").inner_text()
                insights = page.get_by_role("region", name="Understand this QR")
                expect(insights).to_be_visible()
                expect(insights.get_by_text("Recipient unverified", exact=True)).to_be_visible()
                expect(insights.get_by_text("Same currency · no FX conversion", exact=True)).to_be_visible()
                expect(insights.get_by_text("Why this caution level?", exact=True)).to_be_visible()
                assert "merchant@upi" not in insights.inner_text()
                insights.get_by_text("Explore provider fees", exact=True).click()
                insights.get_by_label("FX markup (%)", exact=True).fill("3")
                insights.get_by_label("Fixed fee (INR)", exact=True).fill("5")
                expect(insights.locator(".feeEstimate strong")).to_have_text("INR 108.00")
                expect(insights.get_by_text("Added cost: INR 8.00", exact=True)).to_be_visible()
                insights.get_by_label("FX markup (%)", exact=True).fill("-1")
                expect(insights.get_by_role("alert")).to_be_visible()
                expect(insights.locator(".feeEstimate")).to_have_count(0)
                insights.get_by_label("FX markup (%)", exact=True).fill("0")
                insights.get_by_label("Fixed fee (INR)", exact=True).fill("0")

                # Exercise per-QR explanations without relying on a live FX provider.
                def multi_scan(route):
                    route.fulfill(json={"multiple": True, "total_home": 300, "items": [
                        {"qr_info": {"amount": 100, "raw_fields": {"scheme": "UPI"}},
                         "fx_result": {"from_currency": "INR", "to_currency": "INR",
                                       "rate": 1, "total_home": 100, "rate_date": "2026-10-23",
                                       "provider": "same-currency"},
                         "risk_result": {"risk_level": "low", "reasons": ["Synthetic first caution"]}},
                        {"qr_info": {"amount": 2, "raw_fields": {"scheme": "DEMO"}},
                         "fx_result": {"from_currency": "USD", "to_currency": "INR",
                                       "rate": 100, "total_home": 200, "rate_date": "2026-10-23",
                                       "provider": "synthetic-test-source"},
                         "risk_result": {"risk_level": "not_assessed", "reasons": ["Synthetic second caution"]}}
                    ]})

                page.route("**/api/account/scan-text", multi_scan)
                page.get_by_role("button", name="Translate and save summary").click()
                expect(insights.locator(".scanBreakdown")).to_have_count(2)
                expect(insights.get_by_text("Synthetic second caution", exact=True)).to_be_visible()
                expect(insights.get_by_text("synthetic-test-source", exact=True)).to_be_visible()
                expect(insights.get_by_text("2026-10-23", exact=True)).to_have_count(2)
                expect(insights.get_by_text("Caution: not assessed", exact=True)).to_be_visible()
                expect(insights.locator(".feeEstimate strong")).to_have_text("INR 300.00")
                page.unroute("**/api/account/scan-text", multi_scan)
                page.get_by_role("button", name="Sign out").click()
                expect(page.locator("#account-email")).to_be_visible()
                expect(page.get_by_role("status")).to_have_text("Signed out of this tab.")
                expect(page.get_by_text("Signed in for this tab. Use synthetic QR data only.")).to_have_count(0)

                def sign_in():
                    page.locator("#account-password").fill("synthetic-example-password-1234")
                    page.get_by_role("button", name="Sign in", exact=True).last.click()
                    expect(page.get_by_role("button", name="Sign out")).to_be_enabled()

                def expired(route):
                    route.fulfill(status=401, json={"detail": "Invalid or expired token"})

                def unavailable(route):
                    route.fulfill(status=503, json={"detail": "Temporarily unavailable"})

                # Invalid credentials stay a login error, not a session-expiry error.
                page.locator("#account-password").fill("wrong-synthetic-password")
                page.get_by_role("button", name="Sign in", exact=True).last.click()
                expect(page.get_by_role("alert")).to_have_text("Invalid credentials")

                # Non-authentication failures must preserve the current session.
                sign_in()
                page.route("**/api/account/scan-text", unavailable)
                page.get_by_role("button", name="Translate and save summary").click()
                expect(page.get_by_role("alert")).to_have_text("Temporarily unavailable")
                expect(page.get_by_role("button", name="Sign out")).to_be_enabled()
                expect(page.get_by_text("Signed in for this tab. Use synthetic QR data only.")).to_have_count(0)
                page.unroute("**/api/account/scan-text", unavailable)

                # Every protected action must clear profile, history and results on 401.
                for endpoint, button in [("scan-text", "Translate and save summary"),
                                         ("clear-history", "Clear saved history")]:
                    if endpoint == "clear-history":
                        sign_in()
                    expect(page.locator(".accountTable tbody tr")).to_have_count(1)
                    page.route(f"**/api/account/{endpoint}", expired)
                    page.get_by_role("button", name=button, exact=True).click()
                    expect(page.get_by_role("alert")).to_have_text("Your session has expired. Sign in again.")
                    expect(page.locator("#account-email")).to_be_visible()
                    expect(page.locator("#account-password")).to_have_value("")
                    expect(page.get_by_role("button", name="Sign out")).to_have_count(0)
                    expect(page.locator(".accountTable")).to_have_count(0)
                    expect(page.locator(".accountResult")).to_have_count(0)
                    expect(page.locator(".scanInsights")).to_have_count(0)
                    expect(page.locator(".accountNotice")).to_have_count(0)
                    page.unroute(f"**/api/account/{endpoint}", expired)

                # A token may expire while loading history immediately after login.
                page.route("**/api/account/history", expired)
                page.locator("#account-password").fill("synthetic-example-password-1234")
                page.get_by_role("button", name="Sign in", exact=True).last.click()
                expect(page.get_by_role("alert")).to_have_text("Your session has expired. Sign in again.")
                expect(page.get_by_role("button", name="Sign out")).to_have_count(0)
                page.unroute("**/api/account/history", expired)

                # Failed server logout still removes local credentials with an honest notice.
                sign_in()
                page.route("**/api/account/logout", unavailable)
                page.get_by_role("button", name="Sign out").click()
                expect(page.locator("#account-email")).to_be_visible()
                expect(page.get_by_role("status")).to_have_text(
                    "Signed out of this tab; server revocation was not confirmed.")
                expect(page.locator(".accountTable")).to_have_count(0)
                page.unroute("**/api/account/logout", unavailable)
                assert page.evaluate("localStorage.length") == 0
                print("Browser E2E passed: demo, accounts, logout, expired sessions and service failures")

            finally:
                browser.close()


if __name__ == "__main__":
    run()

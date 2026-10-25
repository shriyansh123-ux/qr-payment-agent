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
                expect(page.get_by_role("heading", name="Travel QR Cost Estimator")).to_be_visible()
                expect(page.get_by_text("Browser locale region:", exact=False)).to_have_count(0)
                expect(page.get_by_text("Show Raw JSON", exact=True)).to_have_count(0)

                page.locator("#api-key").fill(KEY)
                page.locator("textarea").fill(PAYLOAD)
                with page.expect_response(lambda r: "/api/scan-text" in r.url and r.request.method == "POST") as scan_response:
                    page.get_by_role("button", name="Estimate cost", exact=True).click()
                scan = scan_response.value
                assert scan.ok, f"Browser-to-API text scan failed: status={scan.status}, error={scan.text()[:300]}"
                expect(page.locator(".money")).to_have_text("INR 100.00", timeout=10000)
                expect(page.locator(".demoHistory tbody tr")).to_have_count(1)
                expect(page.get_by_text("Text QR (hidden)")).to_be_visible()
                assert PAYLOAD not in page.locator("tbody").inner_text()
                assert page.evaluate("sessionStorage.getItem(\'qr_demo_api_key\')") is None

                page.get_by_role("button", name="Image", exact=True).click()
                page.locator("input[type=file]").set_input_files(str(qr_image))
                page.get_by_role("button", name="Estimate cost", exact=True).click()
                expect(page.locator(".money")).to_have_text("INR 100.00", timeout=30000)
                expect(page.locator(".demoHistory tbody tr")).to_have_count(2)

                # Camera capture is an explicit native file action; feed a synthetic photo.
                page.get_by_role("button", name="Camera", exact=True).click()
                expect(page.get_by_label("Take QR photo", exact=True)).to_have_attribute("capture", "environment")
                page.get_by_label("Take QR photo", exact=True).set_input_files(str(qr_image))
                page.get_by_role("button", name="Estimate cost", exact=True).click()
                expect(page.locator(".money")).to_have_text("INR 100.00", timeout=30000)
                expect(page.locator(".demoHistory tbody tr")).to_have_count(3)
                page.get_by_role("button", name="Text", exact=True).click()
                expect(page.locator(".scanInsights")).to_have_count(0)

                # Exercise target selection and mixed-currency history without live rate dependency.
                def qr_catalog(route):
                    route.fulfill(json={"currencies": [{"code": "INR", "name": "Indian Rupee"},
                                                       {"code": "USD", "name": "US Dollar"}]})
                page.route("**/api/currencies", qr_catalog)
                page.reload()
                page.locator("#api-key").fill(KEY)
                page.get_by_label("Your home currency", exact=True).select_option("USD")
                page.get_by_label("QR Text", exact=True).fill("QR:US:USD:12")
                # Explicit currency validation uses the real backend catalog; same-currency needs no FX.
                page.get_by_role("button", name="Estimate cost", exact=True).click()
                expect(page.locator(".money")).to_have_text("USD 12.00", timeout=30000)
                page.get_by_label("Your home currency", exact=True).select_option("")
                expect(page.locator(".scanInsights")).to_have_count(0)
                page.get_by_label("QR Text", exact=True).fill(PAYLOAD)
                page.get_by_role("button", name="Estimate cost", exact=True).click()
                expect(page.locator(".money")).to_have_text("INR 100.00", timeout=30000)
                expect(page.locator(".demoHistory tbody")).to_contain_text("USD 12.00")
                expect(page.locator(".demoHistory tbody")).to_contain_text("INR 100.00")
                page.unroute("**/api/currencies", qr_catalog)

                page.get_by_role("button", name="Clear History").click()
                expect(page.get_by_text("No history yet.")).to_be_visible()
                # Optional account flows run only against a locally configured SQLite DB.
                page.get_by_role("button", name="Saved scans", exact=True).click()
                expect(page.get_by_role("heading", name="Saved scans")).to_be_visible()
                page.get_by_role("button", name="Create test account").click()
                page.locator("#account-email").fill("synthetic.browser@example.invalid")
                page.locator("#account-password").fill("synthetic-example-password-1234")
                page.get_by_role("button", name="Register", exact=True).click()
                expect(page.get_by_text("Test account created. Sign in to continue.")).to_be_visible()
                page.locator("#account-password").fill("synthetic-example-password-1234")
                page.get_by_role("button", name="Sign in", exact=True).last.click()
                expect(page.get_by_text("Signed in:")).to_be_visible()
                page.locator("#account-qr").fill(PAYLOAD)
                page.get_by_role("button", name="Estimate and save summary").click()
                expect(page.get_by_text("Stored summary history")).to_be_visible()
                expect(page.locator(".accountTable tbody tr")).to_have_count(1, timeout=15000)
                assert "merchant@upi" not in page.locator(".accountTable").inner_text()
                insights = page.get_by_role("region", name="Conversion details")
                expect(insights).to_be_visible()
                expect(page.get_by_text("Recipient unverified", exact=True)).to_have_count(0)
                expect(page.locator(".pill, .raw, .cautionReasons")).to_have_count(0)
                expect(insights.get_by_text("Same currency · no FX conversion", exact=True)).to_be_visible()
                assert "merchant@upi" not in insights.inner_text()
                insights.get_by_text("Explore provider fees", exact=True).click()
                insights.get_by_label("FX markup (%)", exact=True).fill("3")
                insights.get_by_label("Fixed fee (INR)", exact=True).fill("5")
                expect(insights.locator(".feeEstimate strong")).to_have_text("INR 108.00")
                expect(insights.get_by_text("Added cost: INR 8.00", exact=True)).to_be_visible()
                # The project simulation is local-only and never creates payment requests/records.
                simulation = page.get_by_role("region", name="Payment simulation", exact=True)
                expect(simulation).to_contain_text("SIMULATION · NO REAL PAYMENT")
                simulation_requests = []
                def record_simulation_request(request):
                    simulation_requests.append(request.url)
                page.on("request", record_simulation_request)
                simulation.get_by_role("button", name="Start payment simulation", exact=True).click()
                expect(simulation).to_contain_text("INR 108.00")
                simulation.get_by_role("button", name="Cancel simulation", exact=True).click()
                expect(simulation.get_by_role("status")).to_have_text("Simulation cancelled — no payment was attempted.")
                simulation.get_by_role("button", name="Reset simulation", exact=True).click()
                for outcome, expected in [("success", "Simulation successful — no money moved."),
                                          ("declined", "Simulation declined — no money moved."),
                                          ("timeout", "Simulation timed out — no payment was attempted.")]:
                    simulation.get_by_role("button", name="Start payment simulation", exact=True).click()
                    simulation.get_by_label("Demo outcome", exact=True).select_option(outcome)
                    simulation.get_by_role("button", name="Approve simulation", exact=True).click()
                    expect(simulation.get_by_role("status")).to_contain_text("Simulation pending.")
                    simulation.get_by_role("button", name="Show simulated result", exact=True).click()
                    expect(simulation.get_by_role("status")).to_have_text(expected)
                    expect(simulation.get_by_role("button", name="Approve simulation", exact=True)).to_have_count(0)
                    simulation.get_by_role("button", name="Reset simulation", exact=True).click()
                simulation.get_by_role("button", name="Start payment simulation", exact=True).click()
                simulation.get_by_role("button", name="Approve simulation", exact=True).click()
                simulation.get_by_role("button", name="Cancel simulation", exact=True).click()
                expect(simulation.get_by_role("status")).to_have_text("Simulation cancelled — no payment was attempted.")
                insights.get_by_label("FX markup (%)", exact=True).fill("4")
                expect(simulation.get_by_role("button", name="Start payment simulation", exact=True)).to_be_visible()
                expect(simulation.get_by_role("status")).to_have_count(0)
                simulation.get_by_role("button", name="Start payment simulation", exact=True).click()
                expect(simulation).to_contain_text("INR 109.00")
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.set_viewport_size({"width": 1280, "height": 720})
                assert simulation_requests == [], simulation_requests
                page.remove_listener("request", record_simulation_request)
                expect(page.locator(".accountTable tbody tr")).to_have_count(1)
                assert page.evaluate("localStorage.length + sessionStorage.length") == 0
                insights.get_by_label("FX markup (%)", exact=True).fill("-1")
                expect(insights.get_by_role("alert")).to_be_visible()
                expect(insights.locator(".feeEstimate")).to_have_count(0)
                expect(simulation).to_have_count(0)
                insights.get_by_label("FX markup (%)", exact=True).fill("0")
                insights.get_by_label("Fixed fee (INR)", exact=True).fill("0")

                # Exercise per-QR conversion details without relying on a live FX provider.
                def multi_scan(route):
                    route.fulfill(json={"multiple": True, "total_home": 300, "home_currency": "INR", "items": [
                        {"qr_info": {"amount": 100, "raw_fields": {"scheme": "UPI"}},
                         "fx_result": {"from_currency": "INR", "to_currency": "INR",
                                       "rate": 1, "total_home": 100, "rate_date": "2026-10-23",
                                       "provider": "same-currency"}},
                        {"qr_info": {"amount": 2, "raw_fields": {"scheme": "DEMO"}},
                         "fx_result": {"from_currency": "USD", "to_currency": "INR",
                                       "rate": 100, "total_home": 200, "rate_date": "2026-10-23",
                                       "provider": "synthetic-test-source"}}
                    ]})

                page.route("**/api/account/scan-text", multi_scan)
                page.get_by_role("button", name="Estimate and save summary").click()
                expect(insights.locator(".scanBreakdown")).to_have_count(2)
                expect(insights.get_by_text("synthetic-test-source", exact=True)).to_be_visible()
                expect(insights.get_by_text("2026-10-23", exact=True)).to_have_count(2)
                expect(insights.get_by_text("Original amount", exact=True)).to_have_count(2)
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
                page.get_by_role("button", name="Estimate and save summary").click()
                expect(page.get_by_role("alert")).to_have_text("Temporarily unavailable")
                expect(page.get_by_role("button", name="Sign out")).to_be_enabled()
                expect(page.get_by_text("Signed in for this tab. Use synthetic QR data only.")).to_have_count(0)
                page.unroute("**/api/account/scan-text", unavailable)

                # Every protected action must clear profile, history and results on 401.
                for endpoint, button in [("scan-text", "Estimate and save summary"),
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

                # Manual conversion has two supported-currency selectors, independent of QR input.
                currency_rows = [{"code": "USD", "name": "US Dollar"},
                                 {"code": "EUR", "name": "Euro"},
                                 {"code": "INR", "name": "Indian Rupee"}]
                def currency_list(route):
                    route.fulfill(json={"currencies": currency_rows})
                def list_failure(route):
                    route.fulfill(status=503, json={"detail": "Currency list unavailable"})
                page.route("**/api/currencies", list_failure)
                page.get_by_role("button", name="Currency converter", exact=True).click()
                expect(page.get_by_role("alert")).to_have_text("Currency list unavailable")
                page.unroute("**/api/currencies", list_failure)
                page.route("**/api/currencies", currency_list)
                page.get_by_role("button", name="Retry currency list").click()
                expect(page.get_by_label("From currency", exact=True)).to_have_value("USD")
                expect(page.get_by_label("To currency", exact=True)).to_have_value("INR")
                expect(page.get_by_label("From currency", exact=True).locator("option")).to_have_count(3)
                expect(page.get_by_label("To currency", exact=True).locator("option")).to_have_count(3)
                expect(page.get_by_label("Demo API key", exact=True)).to_have_value(KEY)

                def conversion(route):
                    body = route.request.post_data_json
                    assert route.request.headers["x-api-key"] == KEY
                    rate = 1 if body["from_currency"] == body["to_currency"] else 2
                    route.fulfill(json={"amount": body["amount"],
                        "from_currency": body["from_currency"], "to_currency": body["to_currency"],
                        "total_home": float(body["amount"]) * rate, "rate": rate,
                        "rate_date": "2026-10-23", "provider": "synthetic-browser-reference"})

                page.route("**/api/convert", conversion)
                page.get_by_label("Amount to convert", exact=True).fill("10")
                page.get_by_label("To currency", exact=True).select_option("EUR")
                page.get_by_role("button", name="Convert", exact=True).click()
                expect(page.locator(".convertedAmount")).to_have_text("EUR 20.00")
                expect(page.locator(".conversionDetails")).to_contain_text("2026-10-23")
                page.get_by_role("button", name="Swap currencies").click()
                expect(page.get_by_label("From currency", exact=True)).to_have_value("EUR")
                expect(page.get_by_label("To currency", exact=True)).to_have_value("USD")
                expect(page.locator(".conversionDetails")).to_have_count(0)
                page.get_by_label("To currency", exact=True).select_option("EUR")
                page.get_by_role("button", name="Convert", exact=True).click()
                expect(page.locator(".convertedAmount")).to_have_text("EUR 10.00")
                page.get_by_label("Amount to convert", exact=True).fill("0")
                page.get_by_role("button", name="Convert", exact=True).click()
                expect(page.locator(".conversionDetails")).to_have_count(0)
                page.get_by_label("Amount to convert", exact=True).fill("10")
                page.unroute("**/api/convert", conversion)
                page.route("**/api/convert", unavailable)
                page.get_by_role("button", name="Convert", exact=True).click()
                expect(page.get_by_role("alert")).to_have_text("Temporarily unavailable")
                expect(page.locator(".convertedAmount")).to_have_text("—")
                page.unroute("**/api/convert", unavailable)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                assert page.evaluate("localStorage.length") == 0
                # Cash arithmetic and numeral recognition need neither auth nor network.
                cash_requests = []
                def record_cash_request(request):
                    cash_requests.append(request.url)
                page.on("request", record_cash_request)
                page.get_by_role("button", name="Cash helper", exact=True).click()
                cash = page.get_by_role("region", name="Cash helper", exact=True)
                expect(cash).to_contain_text("Thailand · Thai baht (THB)")
                expect(cash.locator(".cashDenomination")).to_have_count(11)
                expect(cash.locator(".cashDenominations").get_by_text("๑๐๐ บาท", exact=True)).to_be_visible()
                expect(cash.locator(".cashDenominations").get_by_text("๒๕ สตางค์", exact=True)).to_be_visible()
                cash.get_by_label("Bill amount (THB)", exact=True).fill("117.75")
                cash.get_by_role("button", name="Try paying with a 500 baht note", exact=True).click()
                expect(cash.locator(".cashExpected")).to_have_text("Expected change: THB 382.25")
                for denomination, quantity in [("100 baht note", "3"), ("50 baht note", "1"),
                    ("20 baht note", "1"), ("10 baht coin", "1"), ("1 baht coin", "2"),
                    ("25 satang coin (THB 0.25)", "1")]:
                    cash.get_by_label(f"Quantity received: {denomination}", exact=True).fill(quantity)
                expect(cash.locator(".cashCheck")).to_contain_text("Change matches exactly.")
                cash.get_by_label("Quantity received: 25 satang coin (THB 0.25)", exact=True).fill("0")
                expect(cash.locator(".cashCheck")).to_contain_text("Change is short by THB 0.25.")
                cash.get_by_label("Quantity received: 25 satang coin (THB 0.25)", exact=True).fill("2")
                expect(cash.locator(".cashCheck")).to_contain_text("Change is extra by THB 0.25.")
                cash.get_by_label("Quantity received: 1 baht coin", exact=True).fill("1.5")
                expect(cash.locator(".cashCheck")).to_contain_text("Fix invalid quantities")
                expect(cash.locator(".cashCheck")).not_to_contain_text("Change matches")
                cash.get_by_role("button", name="Clear counted change", exact=True).click()
                expect(cash.locator(".cashCheck")).to_have_count(0)
                cash.get_by_label("Amount handed over (THB)", exact=True).fill("100")
                expect(cash.get_by_role("alert")).to_have_text("Payment is short by THB 17.75. No change is due yet.")
                expect(cash.locator(".cashExpected")).to_have_count(0)
                expect(cash.get_by_label("Quantity received: 100 baht note", exact=True)).to_be_disabled()
                cash.get_by_label("Bill amount (THB)", exact=True).fill("๑๑๗.๗๕")
                cash.get_by_label("Amount handed over (THB)", exact=True).fill("๑๑๗.๗๕")
                expect(cash.locator(".cashExpected")).to_have_text("Expected change: THB 0.00")
                cash.get_by_label("Quantity received: 1 baht coin", exact=True).fill("0")
                expect(cash.locator(".cashCheck")).to_contain_text("Change matches exactly.")
                cash.get_by_label("Bill amount (THB)", exact=True).fill("117.60")
                cash.get_by_label("Amount handed over (THB)", exact=True).fill("500")
                expect(cash.get_by_role("region", name="Suggested exact payment", exact=True)).to_contain_text("No exact combination")
                expect(cash.locator(".cashExpected")).to_contain_text("THB 382.40")
                expect(cash.get_by_role("region", name="Suggested change", exact=True)).to_contain_text("No rounding has been applied")
                cash.get_by_label("Bill amount (THB)", exact=True).fill("-1")
                expect(cash.locator(".cashExpected")).to_have_count(0)
                expect(cash.locator(".cashCheck")).to_have_count(0)
                expect(cash.get_by_role("alert")).to_contain_text("Enter a bill greater than zero")
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                assert page.evaluate("localStorage.length + sessionStorage.length") == 0
                assert cash_requests == [], cash_requests
                page.remove_listener("request", record_cash_request)
                print("Browser E2E passed: demo, accounts, logout, expired sessions and service failures")

            finally:
                browser.close()


if __name__ == "__main__":
    run()

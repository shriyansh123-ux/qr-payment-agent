"""Bounded local-only HTTP concurrency smoke test.

Run only against localhost, never a public Render URL. This is a regression
smoke benchmark, NOT a capacity claim for 10,000 concurrent users.
"""
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import requests

BASE = os.getenv("QR_LOAD_BASE", "http://127.0.0.1:8766").rstrip("/")
PARSED = urlsplit(BASE)
if PARSED.hostname not in {"localhost", "127.0.0.1", "::1"} or PARSED.scheme != "http":
    raise SystemExit("Refusing external target: benchmark is localhost-only")

KEY = os.environ["QR_API_KEY"]
INPUT = "QR:US:USD:10"  # CI sets HOME_CURRENCY=USD, avoiding provider calls.
REQUESTS = 20
WORKERS = 4


def sample(index):
    started = time.perf_counter()
    response = requests.post(
        BASE + "/api/scan-text",
        headers={"X-API-Key": KEY},
        json={"qr_payload": INPUT},
        timeout=20,
    )
    elapsed = time.perf_counter() - started
    if response.status_code != 200:
        raise AssertionError(f"Scan {index} returned HTTP {response.status_code}")
    result = response.json()
    if result["fx_result"]["total_home"] != 10:
        raise AssertionError("Unexpected amount from deterministic same-currency scan")
    return elapsed


def main():
    if requests.get(BASE + "/api/health", timeout=5).status_code != 200:
        raise SystemExit("Local API not healthy")
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        latencies = list(pool.map(sample, range(REQUESTS)))
    elapsed = time.perf_counter() - started
    sorted_ms = sorted(ms * 1000 for ms in latencies)
    p50_ms = statistics.median(sorted_ms)
    p95_ms = sorted_ms[max(0, int(len(sorted_ms) * 0.95) - 1)]
    print(
        f"Local scan smoke: {REQUESTS} successful requests / {WORKERS} workers, "
        f"p50={p50_ms:.1f}ms, p95={p95_ms:.1f}ms, "
        f"observed_throughput={REQUESTS / elapsed:.2f} requests/s"
    )
    print("Measurement is environment-dependent; not a production SLA or capacity guarantee.")


if __name__ == "__main__":
    main()

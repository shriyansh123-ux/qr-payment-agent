"""Deterministic manual converter tests; no live network calls."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.server import app
from src.services import currencies
from src.services.fx import FXRateService, FXUnavailable

KEY = "synthetic-converter-test-key-at-least-24-characters"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("QR_API_KEY", KEY)
    monkeypatch.setenv("QR_PUBLIC_DEMO", "false")
    monkeypatch.setattr(currencies, "_catalog", None)
    monkeypatch.setattr(currencies, "_catalog_until", 0)
    from src.api import limits
    limits._buckets.clear()
    with TestClient(app) as value:
        yield value


def catalog(monkeypatch):
    monkeypatch.setattr(currencies, "supported_currencies", lambda: [
        {"code": "INR", "name": "Indian Rupee"},
        {"code": "USD", "name": "US Dollar"},
        {"code": "EUR", "name": "Euro"},
    ])


def test_catalog_filters_deduplicates_and_caches(client, monkeypatch):
    today = date.today().isoformat()
    old = (date.today() - timedelta(days=20)).isoformat()
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"iso_code": "USD", "name": "US Dollar", "end_date": today},
                {"iso_code": "INR", "name": "Indian Rupee", "end_date": today},
                {"iso_code": "USD", "name": "US Dollar", "end_date": today},
                {"iso_code": "XAU", "name": "Gold", "end_date": today},
                {"iso_code": "DEM", "name": "Legacy currency", "end_date": old},
            ]

    def get(url, **kwargs):
        calls.append(url)
        return Response()

    monkeypatch.setattr(currencies.requests, "get", get)
    first = client.get("/api/currencies")
    assert first.status_code == 200
    assert [row["code"] for row in first.json()["currencies"]] == ["INR", "USD"]
    assert client.get("/api/currencies").json() == first.json()
    assert len(calls) == 1


def test_catalog_failure_is_explicit(client, monkeypatch):
    def fail(*args, **kwargs):
        raise currencies.requests.RequestException("provider unavailable")
    monkeypatch.setattr(currencies.requests, "get", fail)
    response = client.get("/api/currencies")
    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]


def test_conversion_requires_key(client, monkeypatch):
    catalog(monkeypatch)
    assert client.post("/api/convert", json={
        "amount": "12", "from_currency": "USD", "to_currency": "EUR"
    }).status_code == 401


def test_arbitrary_pair_rounding_and_provenance(client, monkeypatch):
    catalog(monkeypatch)
    monkeypatch.setattr(FXRateService, "get_rate",
                        lambda self, a, b: (Decimal("0.925"), "2026-10-23", "test-reference"))
    response = client.post("/api/convert", headers={"X-API-Key": KEY}, json={
        "amount": "10.5", "from_currency": "USD", "to_currency": "EUR"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_home"] == 9.71
    assert data["from_currency"] == "USD" and data["to_currency"] == "EUR"
    assert data["rate_date"] == "2026-10-23" and data["provider"] == "test-reference"
    assert data["fee_status"] == "not_quoted"


def test_same_currency(client, monkeypatch):
    catalog(monkeypatch)
    response = client.post("/api/convert", headers={"X-API-Key": KEY}, json={
        "amount": "12.34", "from_currency": "EUR", "to_currency": "EUR"
    })
    assert response.status_code == 200
    assert response.json()["total_home"] == 12.34
    assert response.json()["provider"] == "same-currency"


@pytest.mark.parametrize("amount", ["0", "-2", "NaN", "Infinity", "1000000000001", "0.0000001"])
def test_invalid_amounts(client, monkeypatch, amount):
    catalog(monkeypatch)
    assert client.post("/api/convert", headers={"X-API-Key": KEY}, json={
        "amount": amount, "from_currency": "USD", "to_currency": "INR"
    }).status_code == 422


def test_unknown_currency_and_unavailable_pair(client, monkeypatch):
    catalog(monkeypatch)
    headers = {"X-API-Key": KEY}
    assert client.post("/api/convert", headers=headers, json={
        "amount": "1", "from_currency": "ZZZ", "to_currency": "INR"
    }).status_code == 422
    def fail(*args, **kwargs):
        raise FXUnavailable("Reference rate unavailable")
    monkeypatch.setattr(FXRateService, "convert", fail)
    assert client.post("/api/convert", headers=headers, json={
        "amount": "1", "from_currency": "USD", "to_currency": "INR"
    }).status_code == 503


def test_public_demo_allows_keyless_conversion(client, monkeypatch):
    catalog(monkeypatch)
    monkeypatch.setenv("QR_PUBLIC_DEMO", "true")
    response = client.post("/api/convert", json={"amount": "5", "from_currency": "EUR", "to_currency": "EUR"})
    assert response.status_code == 200, response.text
    wrong_key = client.post("/api/convert", headers={"X-API-Key": "wrong"},
                            json={"amount": "5", "from_currency": "EUR", "to_currency": "EUR"})
    assert wrong_key.status_code == 401

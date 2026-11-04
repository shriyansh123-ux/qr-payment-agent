"""Account tests on an isolated SQLite file and, in CI, a disposable PostgreSQL.

Set QR_TEST_POSTGRES_URL to run the PostgreSQL variant; its tables are emptied
before each test, so never point it at a database holding real data.
"""
import os

import pytest
from fastapi.testclient import TestClient

from src.api import accounts
from src.api.server import app


@pytest.fixture(params=["sqlite", "postgres"])
def database_url(request, tmp_path):
    if request.param == "sqlite":
        return "sqlite:///" + str(tmp_path / "accounts.sqlite")
    url = os.getenv("QR_TEST_POSTGRES_URL", "")
    if not url:
        pytest.skip("QR_TEST_POSTGRES_URL not set")
    os.environ["QR_DATABASE_URL"] = url
    try:
        with accounts.connect() as db:
            db.run("TRUNCATE qr_scan_summaries, qr_tokens, qr_users")
    finally:
        del os.environ["QR_DATABASE_URL"]
    return url


def test_accounts_require_configuration(monkeypatch):
    monkeypatch.delenv("QR_DATABASE_URL", raising=False)
    with TestClient(app) as client:
        assert client.post("/api/account/login", json={"email":"a@example.org","password":"very-long-synthetic-password"}).status_code == 503


def test_account_auth_history_isolation_and_logout(database_url, monkeypatch):
    monkeypatch.setenv("QR_DATABASE_URL", database_url)
    monkeypatch.setenv("QR_ALLOW_REGISTRATION", "true")
    with TestClient(app) as client:
        def register(email):
            return client.post("/api/account/register", json={"email":email,"password":"long-synthetic-test-password-123"})
        assert register("one@example.org").status_code == 201
        assert register("two@example.org").status_code == 201
        assert register("one@example.org").status_code == 409
        assert client.post("/api/account/login",json={"email":"one@example.org","password":"wrong-password-xxxx"}).status_code == 401
        def login(email):
            r=client.post("/api/account/login",json={"email":email,"password":"long-synthetic-test-password-123"})
            assert r.status_code==200,r.text
            return {"Authorization":"Bearer "+r.json()["access_token"]}
        a,b=login("one@example.org"),login("two@example.org")
        assert client.get("/api/account/me",headers=a).json()["email"]=="one@example.org"
        assert client.get("/api/account/history",headers=b).json()["items"]==[]
        scan=client.post("/api/account/scan-text",headers=a,json={
            "qr_payload":"upi://pay?pa=merchant@upi&am=100&cu=INR"})
        assert scan.status_code==200,scan.text
        history=client.get("/api/account/history",headers=a)
        assert len(history.json()["items"])==1
        assert "merchant@upi" not in history.text
        assert client.get("/api/account/history",headers=b).json()["items"]==[]
        assert client.post("/api/account/logout",headers=a).status_code==200
        assert client.get("/api/account/history",headers=a).status_code==401
        assert client.get("/api/account/history",headers=b).status_code==200


def test_registration_off_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("QR_DATABASE_URL","sqlite:///"+str(tmp_path/"db.sqlite"))
    monkeypatch.delenv("QR_ALLOW_REGISTRATION", raising=False)
    with TestClient(app) as client:
        assert client.post("/api/account/register",json={
          "email":"test@example.org","password":"long-enough-test-password"}).status_code==403



def test_account_status_reflects_database_config_only(monkeypatch):
    monkeypatch.delenv("QR_DATABASE_URL", raising=False)
    monkeypatch.setenv("QR_ALLOW_REGISTRATION", "true")
    with TestClient(app) as client:
        state = client.get("/api/account/status")
        assert state.status_code == 200
        assert state.json()["enabled"] is False
        assert state.json()["registration_enabled"] is False
    monkeypatch.setenv("QR_DATABASE_URL", "sqlite:////tmp/demo-test-only.sqlite")
    monkeypatch.delenv("QR_ALLOW_REGISTRATION", raising=False)
    with TestClient(app) as client:
        state = client.get("/api/account/status").json()
        assert state["enabled"] is True
        assert state["registration_enabled"] is False


def test_expired_tokens_are_rejected_and_cleaned_up(database_url, monkeypatch):
    monkeypatch.setenv("QR_DATABASE_URL", database_url)
    monkeypatch.setenv("QR_ALLOW_REGISTRATION", "true")
    credentials = {"email": "expiry@example.org", "password": "long-synthetic-test-password-123"}
    with TestClient(app) as client:
        assert client.post("/api/account/register", json=credentials).status_code == 201
        old = client.post("/api/account/login", json=credentials).json()["access_token"]
        with accounts.connect() as db:
            db.run("UPDATE qr_tokens SET expires_at = 1")
        assert client.get("/api/account/me", headers={"Authorization": "Bearer " + old}).status_code == 401
        assert client.post("/api/account/login", json=credentials).status_code == 200
        with accounts.connect() as db:
            remaining = db.run("SELECT COUNT(*) FROM qr_tokens WHERE expires_at <= 1").fetchone()[0]
        assert remaining == 0

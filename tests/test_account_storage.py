"""Optional local account tests with isolated, free SQLite backing store."""
from fastapi.testclient import TestClient
from src.api.server import app


def test_accounts_require_configuration(monkeypatch):
    monkeypatch.delenv("QR_DATABASE_URL", raising=False)
    with TestClient(app) as client:
        assert client.post("/api/account/login", json={"email":"a@example.org","password":"very-long-synthetic-password"}).status_code == 503


def test_account_auth_history_isolation_and_logout(tmp_path, monkeypatch):
    monkeypatch.setenv("QR_DATABASE_URL", "sqlite:///" + str(tmp_path / "accounts.sqlite"))
    monkeypatch.setenv("QR_ALLOW_REGISTRATION", "true")
    monkeypatch.setattr("src.orchestration.orchestrator_agent.call_gemini", lambda prompt: "Synthetic test.")
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

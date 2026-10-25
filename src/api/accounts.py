"""Opt-in, database-backed demo accounts. Never store real payment credentials.

Set QR_DATABASE_URL to sqlite:///absolute/path for local development or a
PostgreSQL URI from a free/paid database provider. No database is required
for the existing shared-key demo. Only synthetic transaction summaries persist.
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/account", tags=["optional-accounts"])


def _database_url():
    url = os.getenv("QR_DATABASE_URL", "")
    if not url:
        raise HTTPException(503, "Account database is not configured")
    return url


@contextmanager
def _connect():
    url = _database_url()
    if url.startswith("sqlite:///"):
        db = sqlite3.connect(url[len("sqlite:///"):], timeout=5)
        db.execute("PRAGMA foreign_keys=ON")
        pg = False
    elif url.startswith(("postgresql://", "postgres://")):
        import psycopg
        db = psycopg.connect(url, connect_timeout=5)
        pg = True
    else:
        raise HTTPException(503, "Unsupported account database configuration")
    try:
        yield db, pg
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _query(db, pg, statement, params=()):
    return db.execute(statement.replace("?", "%s") if pg else statement, params)


def init_database():
    with _connect() as (db, pg):
        _query(db, pg, """CREATE TABLE IF NOT EXISTS qr_users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )""")
        _query(db, pg, """CREATE TABLE IF NOT EXISTS qr_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES qr_users(id) ON DELETE CASCADE,
            expires_at BIGINT NOT NULL
        )""")
        _query(db, pg, """CREATE TABLE IF NOT EXISTS qr_scan_summaries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES qr_users(id) ON DELETE CASCADE,
            timestamp BIGINT NOT NULL,
            currency TEXT NOT NULL,
            total_home TEXT NOT NULL,
            risk_level TEXT NOT NULL
        )""")


def _password_hash(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt,
                            n=2**14, r=8, p=1, dklen=32)
    return salt.hex() + ":" + derived.hex()


def _valid_password(password, encoded):
    try:
        salt_hex, _ = encoded.split(":", 1)
        return hmac.compare_digest(_password_hash(password, bytes.fromhex(salt_hex)), encoded)
    except (ValueError, TypeError):
        return False


def _account_id(authorization):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    token = authorization[7:]
    if len(token) > 256 or len(token) < 32:
        raise HTTPException(401, "Invalid token")
    hashed = hashlib.sha256(token.encode()).hexdigest()
    with _connect() as (db, pg):
        record = _query(db, pg, "SELECT user_id, expires_at FROM qr_tokens WHERE token_hash=?", (hashed,)).fetchone()
    if not record or record[1] <= int(time.time()):
        raise HTTPException(401, "Invalid or expired token")
    return record[0]


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)


def _email(value):
    normal = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normal):
        raise HTTPException(422, "Invalid email format")
    return normal


@router.get("/status")
def account_status():
    """Feature discovery without exposing connection strings or user details."""
    configured = bool(os.getenv("QR_DATABASE_URL", "").strip())
    return {
        "enabled": configured,
        "registration_enabled": configured and
                                os.getenv("QR_ALLOW_REGISTRATION", "false").lower() == "true",
        "notice": "Educational demo only; do not enter real payment information.",
    }


@router.post("/register", status_code=201)
def register(credentials: Credentials):
    if os.getenv("QR_ALLOW_REGISTRATION", "false").lower() != "true":
        raise HTTPException(403, "Registration is disabled")
    init_database()
    email = _email(credentials.email)
    uid = str(uuid.uuid4())
    with _connect() as (db, pg):
        found = _query(db, pg, "SELECT id FROM qr_users WHERE email=?", (email,)).fetchone()
        if found:
            raise HTTPException(409, "Account already exists")
        _query(db, pg, "INSERT INTO qr_users (id,email,password_hash) VALUES (?,?,?)",
               (uid, email, _password_hash(credentials.password)))
    return {"ok": True}


@router.post("/login")
def login(credentials: Credentials):
    init_database()
    email = _email(credentials.email)
    with _connect() as (db, pg):
        found = _query(db, pg, "SELECT id,password_hash FROM qr_users WHERE email=?", (email,)).fetchone()
        # Timing work even when user doesn't exist.
        expected = found[1] if found else _password_hash("invalid-placeholder-password")
        allowed = _valid_password(credentials.password, expected)
        if not found or not allowed:
            raise HTTPException(401, "Invalid credentials")
        token = secrets.token_urlsafe(48)
        hashed = hashlib.sha256(token.encode()).hexdigest()
        expiry = int(time.time()) + 3600
        _query(db, pg, "INSERT INTO qr_tokens (token_hash,user_id,expires_at) VALUES (?,?,?)",
               (hashed, found[0], expiry))
    return {"access_token": token, "token_type": "bearer", "expires_in": 3600}


@router.post("/logout")
def logout(authorization: str = Header(default="")):
    uid = _account_id(authorization)
    hashed = hashlib.sha256(authorization[7:].encode()).hexdigest()
    with _connect() as (db, pg):
        _query(db, pg, "DELETE FROM qr_tokens WHERE token_hash=? AND user_id=?", (hashed, uid))
    return {"ok": True}


@router.get("/me")
def me(authorization: str = Header(default="")):
    uid = _account_id(authorization)
    with _connect() as (db, pg):
        email = _query(db, pg, "SELECT email FROM qr_users WHERE id=?", (uid,)).fetchone()
    if not email:
        raise HTTPException(401, "Account not found")
    return {"email": email[0]}


@router.get("/history")
def history(authorization: str = Header(default="")):
    uid = _account_id(authorization)
    with _connect() as (db, pg):
        entries = _query(db, pg,
            "SELECT timestamp,currency,total_home FROM qr_scan_summaries WHERE user_id=? ORDER BY timestamp DESC LIMIT 50",
            (uid,)).fetchall()
    return {"items": [{"timestamp": t, "currency": c, "total_home": total}
                       for t, c, total in entries]}


@router.post("/clear-history")
def clear_history(authorization: str = Header(default="")):
    uid = _account_id(authorization)
    with _connect() as (db, pg):
        _query(db, pg, "DELETE FROM qr_scan_summaries WHERE user_id=?", (uid,))
    return {"ok": True}


class AccountScan(BaseModel):
    qr_payload: str = Field(min_length=1, max_length=8192)
    user_country: str | None = Field(default=None, max_length=2)
    home_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


@router.post("/scan-text")
def scan_text(req: AccountScan, authorization: str = Header(default="")):
    uid = _account_id(authorization)
    from src.api.server import orchestrator
    from src.agents.fx_rate_agent import FXUnavailable
    try:
        # Don't accept client-supplied session IDs. The demo's in-memory conversational
        # state is never reused as account identity or as account history.
        result = orchestrator.handle_qr_scan(uid, "", req.qr_payload, req.user_country, req.home_currency)
    except FXUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    # Only derived, non-identifying metadata is persisted. No raw QR / payee.
    multiple = result.get("multiple", False)
    first = result["items"][0] if multiple else result
    fx = first["fx_result"]
    total = result["total_home"] if multiple else fx["total_home"]
    currency = fx["to_currency"]
    with _connect() as (db, pg):
        _query(db, pg,
            "INSERT INTO qr_scan_summaries (id,user_id,timestamp,currency,total_home,risk_level) VALUES (?,?,?,?,?,?)",
               # Retain the former NOT NULL column without a destructive database migration.
               (str(uuid.uuid4()), uid, int(time.time()), currency, str(total), "not_assessed"))
    return {"success": True, **result}

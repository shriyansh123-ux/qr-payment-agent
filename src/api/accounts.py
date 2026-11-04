"""Opt-in, database-backed demo accounts. Never store real payment credentials.

Set QR_DATABASE_URL to ``sqlite:////absolute/path`` for local development or a
PostgreSQL URI for hosting. Only derived, synthetic scan summaries persist.
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from src.api.deps import estimator, run_estimate

router = APIRouter(prefix="/api/account", tags=["optional-accounts"])
TOKEN_TTL_SECONDS = 3600
HISTORY_LIMIT = 50

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS qr_users (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS qr_tokens (
        token_hash TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES qr_users(id) ON DELETE CASCADE,
        expires_at BIGINT NOT NULL
    )""",
    # risk_level is retired but kept NOT NULL for compatibility with existing data.
    """CREATE TABLE IF NOT EXISTS qr_scan_summaries (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES qr_users(id) ON DELETE CASCADE,
        timestamp BIGINT NOT NULL,
        currency TEXT NOT NULL,
        total_home TEXT NOT NULL,
        risk_level TEXT NOT NULL
    )""",
    "CREATE INDEX IF NOT EXISTS idx_qr_summaries_user_time ON qr_scan_summaries (user_id, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_qr_tokens_expiry ON qr_tokens (expires_at)",
)
_schema_ready: set[str] = set()
_pools: dict = {}
_state_lock = threading.Lock()


def _database_url() -> str:
    url = os.getenv("QR_DATABASE_URL", "").strip()
    if not url:
        raise HTTPException(503, "Account database is not configured")
    return url


def _pg_pool(url: str):
    with _state_lock:
        pool = _pools.get(url)
        if pool is None:
            from psycopg_pool import ConnectionPool
            # Small pool: free-tier Postgres limits connections; idle ones are recycled.
            pool = ConnectionPool(url, min_size=0, max_size=5, max_idle=300, timeout=10,
                                  kwargs={"connect_timeout": 5},
                                  check=ConnectionPool.check_connection, open=True)
            _pools[url] = pool
        return pool


def close_pools() -> None:
    with _state_lock:
        for pool in _pools.values():
            pool.close()
        _pools.clear()


class _DB:
    """Tiny adapter so the same ``?`` placeholders work on SQLite and PostgreSQL."""

    def __init__(self, conn, pg: bool):
        self.conn, self.pg = conn, pg

    def run(self, statement: str, params=()):
        return self.conn.execute(statement.replace("?", "%s") if self.pg else statement, params)


@contextmanager
def _raw_connection(url: str) -> Iterator[_DB]:
    if url.startswith("sqlite:///"):
        conn = sqlite3.connect(url[len("sqlite:///"):], timeout=5)
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield _DB(conn, pg=False)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    elif url.startswith(("postgresql://", "postgres://")):
        # The pool commits on success and rolls back on error.
        with _pg_pool(url).connection() as conn:
            yield _DB(conn, pg=True)
    else:
        raise HTTPException(503, "Unsupported account database configuration")


@contextmanager
def connect() -> Iterator[_DB]:
    """One connection per request; the schema is created once per database URL."""
    url = _database_url()
    with _raw_connection(url) as db:
        if url not in _schema_ready:
            for statement in _SCHEMA:
                db.run(statement)
            _schema_ready.add(url)
        yield db


def _password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return salt.hex() + ":" + derived.hex()


def _valid_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, _ = encoded.split(":", 1)
        return hmac.compare_digest(_password_hash(password, bytes.fromhex(salt_hex)), encoded)
    except (ValueError, TypeError):
        return False


_DUMMY_HASH = _password_hash("invalid-placeholder-password")


def _token_digest(authorization: str) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    token = authorization[7:]
    if not 32 <= len(token) <= 256:
        raise HTTPException(401, "Invalid token")
    return hashlib.sha256(token.encode()).hexdigest()


def _account_id(db: _DB, authorization: str) -> str:
    digest = _token_digest(authorization)
    record = db.run("SELECT user_id, expires_at FROM qr_tokens WHERE token_hash=?", (digest,)).fetchone()
    if not record or record[1] <= int(time.time()):
        raise HTTPException(401, "Invalid or expired token")
    return record[0]


class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)


def _email(value: str) -> str:
    normal = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normal):
        raise HTTPException(422, "Invalid email format")
    return normal


def _registration_enabled() -> bool:
    return os.getenv("QR_ALLOW_REGISTRATION", "false").lower() == "true"


@router.get("/status")
def account_status():
    """Feature discovery without exposing connection strings or user details."""
    configured = bool(os.getenv("QR_DATABASE_URL", "").strip())
    return {
        "enabled": configured,
        "registration_enabled": configured and _registration_enabled(),
        "notice": "Educational demo only; do not enter real payment information.",
    }


@router.post("/register", status_code=201)
def register(credentials: Credentials):
    if not _registration_enabled():
        raise HTTPException(403, "Registration is disabled")
    email = _email(credentials.email)
    with connect() as db:
        if db.run("SELECT id FROM qr_users WHERE email=?", (email,)).fetchone():
            raise HTTPException(409, "Account already exists")
        db.run("INSERT INTO qr_users (id,email,password_hash) VALUES (?,?,?)",
               (str(uuid.uuid4()), email, _password_hash(credentials.password)))
    return {"ok": True}


@router.post("/login")
def login(credentials: Credentials):
    email = _email(credentials.email)
    with connect() as db:
        found = db.run("SELECT id,password_hash FROM qr_users WHERE email=?", (email,)).fetchone()
        # Do the same hashing work whether or not the account exists.
        allowed = _valid_password(credentials.password, found[1] if found else _DUMMY_HASH)
        if not found or not allowed:
            raise HTTPException(401, "Invalid credentials")
        now = int(time.time())
        db.run("DELETE FROM qr_tokens WHERE expires_at <= ?", (now,))
        token = secrets.token_urlsafe(48)
        db.run("INSERT INTO qr_tokens (token_hash,user_id,expires_at) VALUES (?,?,?)",
               (hashlib.sha256(token.encode()).hexdigest(), found[0], now + TOKEN_TTL_SECONDS))
    return {"access_token": token, "token_type": "bearer", "expires_in": TOKEN_TTL_SECONDS}


@router.post("/logout")
def logout(authorization: str = Header(default="")):
    with connect() as db:
        uid = _account_id(db, authorization)
        db.run("DELETE FROM qr_tokens WHERE token_hash=? AND user_id=?", (_token_digest(authorization), uid))
    return {"ok": True}


@router.get("/me")
def me(authorization: str = Header(default="")):
    with connect() as db:
        uid = _account_id(db, authorization)
        row = db.run("SELECT email FROM qr_users WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(401, "Account not found")
    return {"email": row[0]}


@router.get("/history")
def history(authorization: str = Header(default="")):
    with connect() as db:
        uid = _account_id(db, authorization)
        rows = db.run("SELECT timestamp,currency,total_home FROM qr_scan_summaries "
                      f"WHERE user_id=? ORDER BY timestamp DESC LIMIT {HISTORY_LIMIT}", (uid,)).fetchall()
    return {"items": [{"timestamp": t, "currency": c, "total_home": total} for t, c, total in rows]}


@router.post("/clear-history")
def clear_history(authorization: str = Header(default="")):
    with connect() as db:
        uid = _account_id(db, authorization)
        db.run("DELETE FROM qr_scan_summaries WHERE user_id=?", (uid,))
    return {"ok": True}


class AccountScan(BaseModel):
    qr_payload: str = Field(min_length=1, max_length=8192)
    home_currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


@router.post("/scan-text")
async def scan_text(req: AccountScan, authorization: str = Header(default="")):
    def authenticate():
        with connect() as db:
            return _account_id(db, authorization)

    uid = await run_in_threadpool(authenticate)
    result = await run_estimate(estimator.estimate_text, req.qr_payload, req.home_currency)
    multiple = result.get("multiple", False)
    total = result["total_home"] if multiple else result["fx_result"]["total_home"]
    currency = result["home_currency"] if multiple else result["fx_result"]["to_currency"]

    def save():
        # Only derived, non-identifying data: no raw QR text or payee address.
        with connect() as db:
            db.run("INSERT INTO qr_scan_summaries (id,user_id,timestamp,currency,total_home,risk_level) "
                   "VALUES (?,?,?,?,?,?)",
                   (str(uuid.uuid4()), uid, int(time.time()), currency, str(total), "not_assessed"))

    await run_in_threadpool(save)
    return {"success": True, **result}

# src/persistence/history_store.py
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional


class HistoryStore:
    """
    SQLite-backed history storage (simple + interview-friendly).
    Stores raw result JSON + a compact summary for fast UI tables.
    """

    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    input_repr TEXT NOT NULL,
                    total_home REAL,
                    home_currency TEXT,
                    risk_level TEXT,
                    note TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_history_user_time ON history(user_id, created_at DESC)")
            con.commit()

    def add(
        self,
        user_id: str,
        mode: str,
        input_repr: str,
        total_home: Optional[float],
        home_currency: Optional[str],
        risk_level: Optional[str],
        note: Optional[str],
        raw_result: Dict[str, Any],
    ) -> None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_json = json.dumps(raw_result, ensure_ascii=False)

        with self._conn() as con:
            con.execute(
                """
                INSERT INTO history
                (created_at, user_id, mode, input_repr, total_home, home_currency, risk_level, note, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    user_id,
                    mode,
                    input_repr,
                    float(total_home) if isinstance(total_home, (int, float)) else None,
                    home_currency or "",
                    risk_level or "unknown",
                    note or "",
                    raw_json,
                ),
            )
            con.commit()

    def list(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._conn() as con:
            rows = con.execute(
                """
                SELECT id, created_at, user_id, mode, input_repr, total_home, home_currency, risk_level, note
                FROM history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()

        return [dict(r) for r in rows]

    def get_raw(self, item_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as con:
            row = con.execute(
                "SELECT raw_json FROM history WHERE id = ?",
                (item_id,),
            ).fetchone()

        if not row:
            return None
        return json.loads(row["raw_json"])

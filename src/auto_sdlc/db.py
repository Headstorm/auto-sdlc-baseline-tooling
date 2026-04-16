"""SQLite database module for auto-sdlc log uploads and reports."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class Database:
    """Manages SQLite connection and all CRUD operations."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def init(self) -> None:
        """Open connection and create schema if not exists."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_schema()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: tuple = ()):
        return self._conn.execute(sql, params)

    def _create_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS log_uploads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name     TEXT NOT NULL,
                user_name     TEXT NOT NULL,
                logs_path     TEXT NOT NULL,
                uploaded_at   TEXT NOT NULL,
                session_count INTEGER DEFAULT 0,
                total_tokens  INTEGER DEFAULT 0,
                status        TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS reports (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id             INTEGER REFERENCES log_uploads(id),
                team_name             TEXT NOT NULL,
                user_name             TEXT NOT NULL,
                report_type           TEXT NOT NULL,
                generated_at          TEXT NOT NULL,
                pdf_path              TEXT NOT NULL,
                overall_maturity_level REAL
            );
        """)
        self._conn.commit()

    def insert_upload(
        self,
        team_name: str,
        user_name: str,
        logs_path: str,
        session_count: int = 0,
        total_tokens: int = 0,
    ) -> int:
        uploaded_at = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO log_uploads
               (team_name, user_name, logs_path, uploaded_at, session_count, total_tokens, status)
               VALUES (?, ?, ?, ?, ?, ?, 'pending')""",
            (team_name, user_name, logs_path, uploaded_at, session_count, total_tokens),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_all_uploads(self) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM log_uploads ORDER BY uploaded_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_uploads_by_team(self, team_name: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM log_uploads WHERE team_name = ? ORDER BY uploaded_at DESC",
            (team_name,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_upload_by_id(self, upload_id: int) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM log_uploads WHERE id = ?", (upload_id,)
        ).fetchone()
        return dict(row) if row else None

    def insert_report(
        self,
        upload_id: int,
        team_name: str,
        user_name: str,
        report_type: str,
        pdf_path: str,
        overall_maturity_level: Optional[float] = None,
    ) -> int:
        generated_at = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            """INSERT INTO reports
               (upload_id, team_name, user_name, report_type, generated_at, pdf_path, overall_maturity_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (upload_id, team_name, user_name, report_type, generated_at, pdf_path, overall_maturity_level),
        )
        self._conn.execute(
            "UPDATE log_uploads SET status = 'reported' WHERE id = ?", (upload_id,)
        )
        self._conn.commit()
        return cur.lastrowid

    def get_reports_for_upload(self, upload_id: int) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM reports WHERE upload_id = ? ORDER BY generated_at DESC",
            (upload_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_reports(self) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM reports ORDER BY generated_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_reports_by_team(self, team_name: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM reports WHERE team_name = ? ORDER BY generated_at DESC",
            (team_name,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_reports_by_user(self, user_name: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM reports WHERE user_name = ? ORDER BY generated_at DESC",
            (user_name,),
        ).fetchall()
        return [dict(r) for r in rows]

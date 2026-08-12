from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    name: str
    payload: dict
    status: str
    attempts: int
    created_at: str


class RuntimeStore:
    """Durable SQLite state for jobs, results and audit events."""

    def __init__(self, path: str | Path = "aurelix.db") -> None:
        self.path = str(path)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS job_results (
                job_id TEXT PRIMARY KEY REFERENCES jobs(job_id),
                result TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                job_id TEXT,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def enqueue(self, name: str, payload: dict | None = None) -> JobRecord:
        now = self._now()
        job_id = str(uuid4())
        self._db.execute(
            "INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
            (job_id, name, json.dumps(payload or {}, sort_keys=True), "queued", 0, now, now),
        )
        self._db.commit()
        return JobRecord(job_id, name, payload or {}, "queued", 0, now)

    def claim_next(self) -> JobRecord | None:
        row = self._db.execute(
            "SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        now = self._now()
        self._db.execute(
            "UPDATE jobs SET status='running', attempts=attempts+1, updated_at=? WHERE job_id=? AND status='queued'",
            (now, row["job_id"]),
        )
        self._db.commit()
        fresh = self._db.execute("SELECT * FROM jobs WHERE job_id=?", (row["job_id"],)).fetchone()
        return JobRecord(fresh["job_id"], fresh["name"], json.loads(fresh["payload"]), fresh["status"], fresh["attempts"], fresh["created_at"])

    def finish(self, job_id: str, result: dict) -> None:
        now = self._now()
        self._db.execute("UPDATE jobs SET status='completed', updated_at=? WHERE job_id=?", (now, job_id))
        self._db.execute(
            "INSERT OR REPLACE INTO job_results(job_id,result,created_at) VALUES(?,?,?)",
            (job_id, json.dumps(result, sort_keys=True), now),
        )
        self._db.commit()

    def fail(self, job_id: str, error: str, retry: bool = True) -> None:
        now = self._now()
        status = "queued" if retry else "failed"
        self._db.execute("UPDATE jobs SET status=?, updated_at=? WHERE job_id=?", (status, now, job_id))
        self.record_audit(job_id, "job_failed", {"error": error, "retry": retry})
        self._db.commit()

    def record_audit(self, job_id: str | None, event_type: str, payload: dict) -> None:
        self._db.execute(
            "INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)",
            (str(uuid4()), job_id, event_type, json.dumps(payload, sort_keys=True), self._now()),
        )
        self._db.commit()

    def recover_running_jobs(self) -> int:
        """Return interrupted jobs to the queue after an unclean process restart."""
        cursor = self._db.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (self._now(),))
        self._db.commit()
        return cursor.rowcount

    def close(self) -> None:
        self._db.close()

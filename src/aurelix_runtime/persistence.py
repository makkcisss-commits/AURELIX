from __future__ import annotations

import json
import sqlite3
import threading
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
    """Durable SQLite state for jobs, results, experiments and audit events."""

    def __init__(self, path: str | Path = "aurelix.db") -> None:
        self.path = str(path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock, self.db:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_error TEXT
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
                CREATE TABLE IF NOT EXISTS runtime_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    hypothesis TEXT NOT NULL,
                    success_criteria TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    observation TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, created_at);
                CREATE INDEX IF NOT EXISTS idx_observations_experiment
                    ON observations(experiment_id, recorded_at);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def enqueue(self, name: str, payload: dict | None = None) -> JobRecord:
        now = self._now()
        job_id = str(uuid4())
        payload = payload or {}
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at,last_error) VALUES(?,?,?,?,?,?,?,?)",
                (job_id, name, json.dumps(payload, sort_keys=True), "queued", 0, now, now, None),
            )
        return JobRecord(job_id, name, payload, "queued", 0, now)

    def claim_next(self, max_attempts: int = 3) -> JobRecord | None:
        """Atomically claim one queued job; the stable job ID is reused on retry."""
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute(
                    "SELECT * FROM jobs WHERE status='queued' AND attempts < ? ORDER BY created_at LIMIT 1",
                    (max_attempts,),
                ).fetchone()
                if row is None:
                    self.db.rollback()
                    return None
                now = self._now()
                cursor = self.db.execute(
                    "UPDATE jobs SET status='running', attempts=attempts+1, updated_at=? WHERE job_id=? AND status='queued'",
                    (now, row["job_id"]),
                )
                if cursor.rowcount != 1:
                    self.db.rollback()
                    return None
                self.db.commit()
                return JobRecord(row["job_id"], row["name"], json.loads(row["payload"]), "running", row["attempts"] + 1, row["created_at"])
            except Exception:
                self.db.rollback()
                raise

    def claim(self, max_attempts: int = 3) -> JobRecord | None:
        return self.claim_next(max_attempts)

    def finish(self, job_id: str, success: bool, error: str | None = None, retry: bool = False) -> None:
        """Persist the state transition and terminal result atomically."""
        now = self._now()
        with self.lock, self.db:
            row = self.db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(f"job not found: {job_id}")
            if row["status"] != "running":
                raise RuntimeError(f"job {job_id} cannot finish from state {row['status']}")
            if success:
                status, result = "completed", {"ok": True}
            elif retry:
                status, result = "queued", None
            else:
                status, result = "failed", {"ok": False, "error": error or "unknown error"}
            self.db.execute(
                "UPDATE jobs SET status=?, updated_at=?, last_error=? WHERE job_id=? AND status='running'",
                (status, now, error, job_id),
            )
            if result is not None:
                self.db.execute(
                    "INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO UPDATE SET result=excluded.result, created_at=excluded.created_at",
                    (job_id, json.dumps(result, sort_keys=True), now),
                )

    def record_result(self, job_id: str, result: dict) -> None:
        now = self._now()
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO UPDATE SET result=excluded.result, created_at=excluded.created_at",
                (job_id, json.dumps(result, sort_keys=True), now),
            )

    def fail(self, job_id: str, error: str, retry: bool = True) -> None:
        self.finish(job_id, False, error, retry=retry)
        self.record_audit(job_id, "job_failed", {"error": error, "retry": retry})

    def record_audit(self, job_id: str | None, event_type: str, payload: dict) -> None:
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)",
                (str(uuid4()), job_id, event_type, json.dumps(payload, sort_keys=True), self._now()),
            )

    def audit(self, event_type: str, actor: str, subject: str, outcome: str, metadata: dict) -> None:
        self.record_audit(subject, event_type, {"actor": actor, "subject": subject, "outcome": outcome, **metadata})

    def recover_running_jobs(self) -> int:
        """Return jobs left running by an unclean restart to the queue and audit them."""
        now = self._now()
        with self.lock, self.db:
            rows = self.db.execute("SELECT job_id FROM jobs WHERE status='running'").fetchall()
            cursor = self.db.execute("UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (now,))
            for row in rows:
                self.record_audit(row["job_id"], "job.interrupted", {"recovered_at": now})
        return cursor.rowcount

    def recover_running(self) -> int:
        return self.recover_running_jobs()

    def heartbeat(self) -> None:
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES('heartbeat',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self._now(),),
            )

    def status(self) -> dict[str, int | str]:
        with self.lock:
            counts = {row[0]: row[1] for row in self.db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")}
            row = self.db.execute("SELECT value FROM runtime_state WHERE key='heartbeat'").fetchone()
        return {"heartbeat": row[0] if row else "never", "queued": counts.get("queued", 0), "running": counts.get("running", 0), "succeeded": counts.get("completed", 0), "failed": counts.get("failed", 0)}

    def audit_summary(self, limit: int = 20) -> dict:
        with self.lock:
            rows = self.db.execute("SELECT event_type, job_id, payload, created_at FROM audit_events ORDER BY created_at DESC LIMIT ?", (max(0, limit),)).fetchall()
        return {"recent": [{"event_type": row[0], "actor": json.loads(row[2]).get("actor", "runtime"), "subject": row[1] or "", "outcome": json.loads(row[2]).get("outcome", "recorded"), "metadata": json.loads(row[2]), "created_at": row[3]} for row in rows]}

    def close(self) -> None:
        with self.lock:
            self.db.close()

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


TERMINAL_STATUSES = {"completed", "failed"}


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    name: str
    payload: dict
    status: str
    attempts: int
    created_at: str
    updated_at: str | None = None


class RuntimeStore:
    """Durable SQLite execution state with atomic transitions and recovery."""

    def __init__(self, path: str | Path = "aurelix.db") -> None:
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False, timeout=30.0)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self._supports_interrupted = True
        with self.lock, self.db:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA busy_timeout=30000")
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued','running','interrupted','completed','failed')),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    heartbeat_at TEXT,
                    worker_id TEXT,
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
                CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, created_at, job_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_heartbeat ON jobs(status, heartbeat_at);
                CREATE INDEX IF NOT EXISTS idx_observations_experiment ON observations(experiment_id, recorded_at);
                """
            )
            self._migrate_jobs_schema()

    def _migrate_jobs_schema(self) -> None:
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)").fetchall()}
        sql_row = self.db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()
        self._supports_interrupted = bool(sql_row and "interrupted" in (sql_row[0] or ""))
        for name in ("started_at", "heartbeat_at", "worker_id"):
            if name not in columns:
                self.db.execute(f"ALTER TABLE jobs ADD COLUMN {name} TEXT")
        self.db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(row["job_id"], row["name"], json.loads(row["payload"]), row["status"], row["attempts"], row["created_at"], row["updated_at"])

    def enqueue(self, name: str, payload: dict | None = None, execution_id: str | None = None) -> JobRecord:
        now = self._now()
        job_id = execution_id or str(uuid4())
        payload = payload or {}
        with self.lock, self.db:
            self.db.execute("INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?)", (job_id, name, json.dumps(payload, sort_keys=True), "queued", 0, now, now))
        return JobRecord(job_id, name, payload, "queued", 0, now, now)

    def get(self, job_id: str) -> JobRecord | None:
        with self.lock:
            row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return self._record(row) if row else None

    def get_result(self, job_id: str) -> dict | None:
        with self.lock:
            row = self.db.execute("SELECT result FROM job_results WHERE job_id=?", (job_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def claim_next(self, max_attempts: int = 3, worker_id: str | None = None) -> JobRecord | None:
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT * FROM jobs WHERE status='queued' AND attempts < ? ORDER BY created_at, job_id LIMIT 1", (max_attempts,)).fetchone()
                if row is None:
                    self.db.rollback()
                    return None
                return self._claim_row(row, worker_id)
            except Exception:
                self.db.rollback()
                raise

    def claim(self, job_id: str, max_attempts: int = 3, worker_id: str | None = None) -> JobRecord | None:
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                if row is None or row["status"] != "queued" or row["attempts"] >= max_attempts:
                    self.db.rollback()
                    return None
                return self._claim_row(row, worker_id)
            except Exception:
                self.db.rollback()
                raise

    def _claim_row(self, row: sqlite3.Row, worker_id: str | None) -> JobRecord:
        now = self._now()
        cursor = self.db.execute("UPDATE jobs SET status='running', attempts=attempts+1, updated_at=?, started_at=COALESCE(started_at, ?), heartbeat_at=?, worker_id=? WHERE job_id=? AND status='queued'", (now, now, now, worker_id, row["job_id"]))
        if cursor.rowcount != 1:
            self.db.rollback()
            raise RuntimeError(f"job {row['job_id']} was claimed concurrently")
        self.db.commit()
        return JobRecord(row["job_id"], row["name"], json.loads(row["payload"]), "running", row["attempts"] + 1, row["created_at"], now)

    def heartbeat(self, job_id: str | None = None, worker_id: str | None = None) -> bool:
        """Heartbeat a job, or the runtime when called without a job ID."""
        if job_id is None:
            self.heartbeat_runtime()
            return True
        now = self._now()
        with self.lock, self.db:
            cursor = self.db.execute("UPDATE jobs SET heartbeat_at=?, updated_at=? WHERE job_id=? AND status='running' AND (? IS NULL OR worker_id=?)", (now, now, job_id, worker_id, worker_id))
        return cursor.rowcount == 1

    def heartbeat_runtime(self) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT INTO runtime_state(key,value) VALUES('heartbeat',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (self._now(),))

    def record(self, event_type: str, **metadata: object) -> None:
        self.record_audit(None, event_type, metadata)

    def complete(self, job_id: str, result: dict | None = None) -> dict:
        """Persist the result and successful terminal transition atomically and idempotently."""
        now = self._now()
        result = result or {"ok": True}
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                if row is None:
                    raise KeyError(f"job not found: {job_id}")
                if row["status"] == "completed":
                    existing = self.get_result(job_id)
                    self.db.commit()
                    return existing or result
                if row["status"] != "running":
                    raise RuntimeError(f"job {job_id} cannot complete from state {row['status']}")
                self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (job_id, json.dumps(result, sort_keys=True), now))
                stored = self.db.execute("SELECT result FROM job_results WHERE job_id=?", (job_id,)).fetchone()
                self.db.execute("UPDATE jobs SET status='completed', updated_at=?, heartbeat_at=NULL, worker_id=NULL, last_error=NULL WHERE job_id=? AND status='running'", (now, job_id))
                self.db.commit()
                return json.loads(stored[0]) if stored else result
            except Exception:
                self.db.rollback()
                raise

    def finish(self, job_id: str, success: bool, error: str | None = None, retry: bool = False, result: dict | None = None) -> None:
        if success:
            row = self.get(job_id)
            if row is None:
                raise KeyError(f"job not found: {job_id}")
            if row.status != "running":
                raise RuntimeError(f"job {job_id} cannot finish from state {row.status}")
            self.complete(job_id, result or {"ok": True})
            return
        now = self._now()
        with self.lock, self.db:
            row = self.db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(f"job not found: {job_id}")
            if row["status"] != "running":
                raise RuntimeError(f"job {job_id} cannot finish from state {row['status']}")
            status = "queued" if retry else "failed"
            self.db.execute("UPDATE jobs SET status=?, updated_at=?, heartbeat_at=NULL, worker_id=NULL, last_error=? WHERE job_id=? AND status='running'", (status, now, error, job_id))
            if not retry:
                self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (job_id, json.dumps({"ok": False, "error": error or "unknown error"}, sort_keys=True), now))

    def record_result(self, job_id: str, result: dict) -> None:
        now = self._now()
        with self.lock, self.db:
            row = self.db.execute("SELECT status FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(f"job not found: {job_id}")
            if row["status"] != "running":
                existing = self.get_result(job_id)
                if existing == result and row["status"] in TERMINAL_STATUSES:
                    return
                raise RuntimeError(f"job {job_id} cannot record a result from state {row['status']}")
            self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (job_id, json.dumps(result, sort_keys=True), now))

    def fail(self, job_id: str, error: str, retry: bool = True) -> None:
        self.finish(job_id, False, error, retry=retry)
        self.record_audit(job_id, "job_failed", {"error": error, "retry": retry})

    def record_audit(self, job_id: str | None, event_type: str, payload: dict) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)", (str(uuid4()), job_id, event_type, json.dumps(payload, sort_keys=True), self._now()))

    def audit(self, event_type: str, actor: str, subject: str, outcome: str, metadata: dict) -> None:
        self.record_audit(subject, event_type, {"actor": actor, "subject": subject, "outcome": outcome, **metadata})

    def recover_running_jobs(self, max_attempts: int = 3, stale_after_seconds: float = 0.0) -> int:
        """Recover stale RUNNING rows without re-executing a job with a durable result."""
        now_dt = datetime.now(timezone.utc)
        cutoff = now_dt - timedelta(seconds=max(0.0, stale_after_seconds))
        now = now_dt.isoformat()
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                rows = self.db.execute("SELECT job_id, attempts, heartbeat_at FROM jobs WHERE status='running'").fetchall()
                recovered = 0
                for row in rows:
                    if stale_after_seconds > 0 and row["heartbeat_at"]:
                        try:
                            if datetime.fromisoformat(row["heartbeat_at"]) > cutoff:
                                continue
                        except ValueError:
                            pass

                    durable = self.db.execute("SELECT result FROM job_results WHERE job_id=?", (row["job_id"],)).fetchone()
                    if durable is not None:
                        self.db.execute("UPDATE jobs SET status='completed', updated_at=?, heartbeat_at=NULL, worker_id=NULL, last_error=NULL WHERE job_id=? AND status='running'", (now, row["job_id"]))
                        self.db.execute("INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)", (str(uuid4()), row["job_id"], "job.recovered", json.dumps({"recovered_at": now, "attempts": row["attempts"], "outcome": "completed_from_durable_result"}, sort_keys=True), now))
                        recovered += 1
                        continue

                    final_status = "failed" if row["attempts"] >= max_attempts else "queued"
                    error = "interrupted after maximum attempts" if final_status == "failed" else "interrupted; queued for recovery"
                    if self._supports_interrupted:
                        self.db.execute("UPDATE jobs SET status='interrupted', updated_at=?, last_error=? WHERE job_id=? AND status='running'", (now, error, row["job_id"]))
                        self.db.execute("UPDATE jobs SET status=?, updated_at=?, heartbeat_at=NULL, worker_id=NULL, last_error=? WHERE job_id=? AND status='interrupted'", (final_status, now, error, row["job_id"]))
                    else:
                        self.db.execute("UPDATE jobs SET status=?, updated_at=?, heartbeat_at=NULL, worker_id=NULL, last_error=? WHERE job_id=? AND status='running'", (final_status, now, error, row["job_id"]))
                    if final_status == "failed":
                        self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (row["job_id"], json.dumps({"ok": False, "error": error}, sort_keys=True), now))
                    self.db.execute("INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)", (str(uuid4()), row["job_id"], "job.interrupted", json.dumps({"recovered_at": now, "attempts": row["attempts"], "outcome": final_status}, sort_keys=True), now))
                    recovered += 1
                self.db.commit()
                return recovered
            except Exception:
                self.db.rollback()
                raise

    def recover_running(self) -> int:
        return self.recover_running_jobs()

    def status(self) -> dict[str, int | str]:
        with self.lock:
            counts = {row[0]: row[1] for row in self.db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")}
            row = self.db.execute("SELECT value FROM runtime_state WHERE key='heartbeat'").fetchone()
        return {"heartbeat": row[0] if row else "never", "queued": counts.get("queued", 0), "running": counts.get("running", 0), "interrupted": counts.get("interrupted", 0), "succeeded": counts.get("completed", 0), "failed": counts.get("failed", 0)}

    def audit_summary(self, limit: int = 20) -> dict:
        with self.lock:
            rows = self.db.execute("SELECT event_type, job_id, payload, created_at FROM audit_events ORDER BY created_at DESC LIMIT ?", (max(0, limit),)).fetchall()
        return {"recent": [{"event_type": row[0], "actor": json.loads(row[2]).get("actor", "runtime"), "subject": row[1] or "", "outcome": json.loads(row[2]).get("outcome", "recorded"), "metadata": json.loads(row[2]), "created_at": row[3]} for row in rows]}

    def close(self) -> None:
        with self.lock:
            self.db.close()

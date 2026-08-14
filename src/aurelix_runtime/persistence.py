from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4


class LeaseLostError(RuntimeError):
    pass


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    name: str
    payload: dict
    status: str
    attempts: int
    created_at: str
    updated_at: str
    worker_id: str | None = None
    lease_token: str | None = None
    lease_until: str | None = None


class RuntimeStore:
    def __init__(self, database_path: str = "data/aurelix.db", lease_seconds: float = 30.0) -> None:
        self.lease_seconds = lease_seconds
        self.lock = threading.RLock()
        self.db = sqlite3.connect(database_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.lock, self.db:
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    heartbeat_at TEXT,
                    worker_id TEXT,
                    lease_token TEXT,
                    lease_until TEXT,
                    last_error TEXT
                );
                CREATE TABLE IF NOT EXISTS job_results (job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), result TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit_events (event_id TEXT PRIMARY KEY, job_id TEXT, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runtime_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS experiments (experiment_id TEXT PRIMARY KEY, hypothesis TEXT NOT NULL, success_criteria TEXT NOT NULL, status TEXT NOT NULL, result TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, observation TEXT NOT NULL, recorded_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, created_at, job_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_heartbeat ON jobs(status, heartbeat_at);
                CREATE INDEX IF NOT EXISTS idx_jobs_lease ON jobs(status, lease_until);
                CREATE INDEX IF NOT EXISTS idx_observations_experiment ON observations(experiment_id, recorded_at);
                CREATE VIEW IF NOT EXISTS audit_log AS SELECT event_id, job_id, event_type, payload, created_at FROM audit_events;
                """
            )
            self._migrate_jobs_schema()

    def _migrate_jobs_schema(self) -> None:
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)").fetchall()}
        for name in ("started_at", "heartbeat_at", "worker_id", "lease_token", "lease_until", "last_error"):
            if name not in columns:
                self.db.execute(f"ALTER TABLE jobs ADD COLUMN {name} TEXT")
        self.db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _lease_until(self, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        return (now + timedelta(seconds=self.lease_seconds)).isoformat()

    @staticmethod
    def _record(row: sqlite3.Row) -> JobRecord:
        return JobRecord(row["job_id"], row["name"], json.loads(row["payload"]), row["status"], row["attempts"], row["created_at"], row["updated_at"], row["worker_id"], row["lease_token"], row["lease_until"])

    def enqueue(self, name: str, payload: dict | None = None, execution_id: str | None = None) -> JobRecord:
        now = self._now(); job_id = execution_id or str(uuid4()); payload = payload or {}
        with self.lock, self.db:
            existing = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if existing is not None:
                existing_payload = json.loads(existing["payload"])
                if existing["name"] != name or existing_payload != payload:
                    raise ValueError(f"execution_id {job_id} is already bound to a different job")
                return self._record(existing)
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
                    self.db.rollback(); return None
                return self._claim_row(row, worker_id)
            except Exception:
                self.db.rollback(); raise

    def claim(self, job_id: str, max_attempts: int = 3, worker_id: str | None = None) -> JobRecord | None:
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                if row is None or row["status"] != "queued" or row["attempts"] >= max_attempts:
                    self.db.rollback(); return None
                return self._claim_row(row, worker_id)
            except Exception:
                self.db.rollback(); raise

    def _claim_row(self, row: sqlite3.Row, worker_id: str | None) -> JobRecord:
        now_dt = datetime.now(timezone.utc); now = now_dt.isoformat(); token = str(uuid4()); lease_until = self._lease_until(now_dt)
        cursor = self.db.execute("UPDATE jobs SET status='running', attempts=attempts+1, updated_at=?, started_at=COALESCE(started_at, ?), heartbeat_at=?, worker_id=?, lease_token=?, lease_until=? WHERE job_id=? AND status='queued'", (now, now, now, worker_id, token, lease_until, row["job_id"]))
        if cursor.rowcount != 1:
            self.db.rollback(); raise RuntimeError(f"job {row['job_id']} was claimed concurrently")
        self.db.commit()
        return JobRecord(row["job_id"], row["name"], json.loads(row["payload"]), "running", row["attempts"] + 1, row["created_at"], now, worker_id, token, lease_until)

    def heartbeat(self, job_id: str | None = None, worker_id: str | None = None, lease_token: str | None = None) -> bool:
        if job_id is None:
            self.heartbeat_runtime(); return True
        now_dt = datetime.now(timezone.utc); now = now_dt.isoformat()
        with self.lock, self.db:
            cursor = self.db.execute("UPDATE jobs SET heartbeat_at=?, updated_at=?, lease_until=? WHERE job_id=? AND status='running' AND worker_id=? AND lease_token=? AND lease_until > ?", (now, now, self._lease_until(now_dt), job_id, worker_id, lease_token, now))
        return cursor.rowcount == 1

    def heartbeat_runtime(self) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT INTO runtime_state(key,value) VALUES('heartbeat',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (self._now(),))

    def record_audit(self, job_id: str | None, event_type: str, payload: dict) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)", (str(uuid4()), job_id, event_type, json.dumps(payload, sort_keys=True), self._now()))

    def audit(self, event_type: str, actor: str, job_id: str | None, status: str, payload: dict) -> None:
        self.record_audit(job_id, event_type, {"actor": actor, "status": status, **payload})

    def complete(self, job_id: str, result: dict | None = None, worker_id: str | None = None, lease_token: str | None = None) -> dict:
        now = self._now(); result = result or {"ok": True}
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.db.execute("SELECT status, worker_id, lease_token FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                if row is None: raise KeyError(f"job not found: {job_id}")
                if row["status"] == "completed":
                    existing = self.get_result(job_id); self.db.commit(); return existing or result
                if row["status"] != "running": raise RuntimeError(f"job {job_id} cannot complete from state {row['status']}")
                if worker_id is None or lease_token is None or row["worker_id"] != worker_id or row["lease_token"] != lease_token:
                    self.db.rollback(); raise LeaseLostError(f"job {job_id} is no longer owned by this worker")
                self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (job_id, json.dumps(result, sort_keys=True), now))
                stored = self.db.execute("SELECT result FROM job_results WHERE job_id=?", (job_id,)).fetchone()
                cursor = self.db.execute("UPDATE jobs SET status='completed', updated_at=?, heartbeat_at=NULL, worker_id=NULL, lease_token=NULL, lease_until=NULL, last_error=NULL WHERE job_id=? AND status='running' AND worker_id=? AND lease_token=?", (now, job_id, worker_id, lease_token))
                if cursor.rowcount != 1:
                    self.db.rollback(); raise LeaseLostError(f"job {job_id} lost ownership during completion")
                self.db.commit(); return json.loads(stored[0]) if stored else result
            except Exception:
                self.db.rollback(); raise

    def finish(self, job_id: str, success: bool, error: str | None = None, retry: bool = False, result: dict | None = None, worker_id: str | None = None, lease_token: str | None = None) -> None:
        if success:
            self.complete(job_id, result or {"ok": True}, worker_id=worker_id, lease_token=lease_token); return
        now = self._now()
        with self.lock, self.db:
            row = self.db.execute("SELECT status, worker_id, lease_token FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None: raise KeyError(f"job not found: {job_id}")
            if row["status"] != "running": raise RuntimeError(f"job {job_id} cannot finish from state {row['status']}")
            if worker_id is None or lease_token is None or row["worker_id"] != worker_id or row["lease_token"] != lease_token: raise LeaseLostError(f"job {job_id} is no longer owned by this worker")
            status = "queued" if retry else "failed"
            self.db.execute("UPDATE jobs SET status=?, updated_at=?, heartbeat_at=NULL, worker_id=NULL, lease_token=NULL, lease_until=NULL, last_error=? WHERE job_id=? AND status='running' AND worker_id=? AND lease_token=?", (status, now, error, job_id, worker_id, lease_token))
            if not retry: self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO NOTHING", (job_id, json.dumps({"ok": False, "error": error or "unknown error"}, sort_keys=True), now))

    def recover_running_jobs(self, max_attempts: int = 3, stale_after_seconds: float = 60.0) -> int:
        now_dt = datetime.now(timezone.utc); cutoff = (now_dt - timedelta(seconds=stale_after_seconds)).isoformat()
        with self.lock, self.db:
            rows = self.db.execute("SELECT job_id, attempts FROM jobs WHERE status='running' AND (lease_until IS NULL OR lease_until < ? OR heartbeat_at IS NULL OR heartbeat_at < ?)", (now_dt.isoformat(), cutoff)).fetchall()
            recovered = 0
            for row in rows:
                status = "queued" if row["attempts"] < max_attempts else "failed"
                self.db.execute("UPDATE jobs SET status=?, updated_at=?, worker_id=NULL, lease_token=NULL, lease_until=NULL, heartbeat_at=NULL WHERE job_id=? AND status='running'", (status, now_dt.isoformat(), row["job_id"]))
                recovered += 1
            return recovered

    def record_result(self, job_id: str, result: dict, worker_id: str | None = None, lease_token: str | None = None) -> None:
        now = self._now()
        with self.lock, self.db:
            row = self.db.execute("SELECT status, worker_id, lease_token FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None: raise KeyError(f"job not found: {job_id}")
            if row["status"] != "running" or row["worker_id"] != worker_id or row["lease_token"] != lease_token: raise LeaseLostError(f"job {job_id} is no longer owned by this worker")
            self.db.execute("INSERT INTO job_results(job_id,result,created_at) VALUES(?,?,?) ON CONFLICT(job_id) DO UPDATE SET result=excluded.result, created_at=excluded.created_at", (job_id, json.dumps(result, sort_keys=True), now))

    def stats(self) -> dict[str, object]:
        with self.lock:
            counts = {row[0]: row[1] for row in self.db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")}; row = self.db.execute("SELECT value FROM runtime_state WHERE key='heartbeat'").fetchone()
        return {"heartbeat": row[0] if row else "never", "queued": counts.get("queued", 0), "running": counts.get("running", 0), "interrupted": counts.get("interrupted", 0), "succeeded": counts.get("completed", 0), "failed": counts.get("failed", 0)}

    def close(self) -> None:
        with self.lock: self.db.close()

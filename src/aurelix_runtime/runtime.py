from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from .pipeline_runner import GovernedPipeline


@dataclass(frozen=True)
class RuntimeConfig:
    database_path: str = "data/aurelix.db"
    heartbeat_seconds: float = 30.0
    worker_poll_seconds: float = 1.0
    max_attempts: int = 3


@dataclass(frozen=True)
class Job:
    job_id: str
    kind: str
    payload: dict[str, str]
    status: str
    attempts: int


class RuntimeStore:
    """Durable SQLite state for jobs, audit, approvals and runtime heartbeat."""

    def __init__(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(target, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock, self.db:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_error TEXT
            );
            CREATE TABLE IF NOT EXISTS audit (
                event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, actor TEXT NOT NULL,
                subject TEXT NOT NULL, outcome TEXT NOT NULL, metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY, action TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, decided_at TEXT
            );
            CREATE TABLE IF NOT EXISTS runtime_state (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            """)

    def enqueue(self, kind: str, payload: dict[str, str]) -> str:
        job_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                (job_id, kind, json.dumps(payload), "queued", 0, now, now, None),
            )
        return job_id

    def recover_running(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            cursor = self.db.execute(
                "UPDATE jobs SET status='queued', updated_at=? WHERE status='running'", (now,)
            )
        return cursor.rowcount

    def claim(self, max_attempts: int = 3) -> Job | None:
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT * FROM jobs WHERE status='queued' AND attempts < ? ORDER BY created_at LIMIT 1",
                (max_attempts,),
            ).fetchone()
            if not row:
                return None
            now = datetime.now(timezone.utc).isoformat()
            self.db.execute(
                "UPDATE jobs SET status='running', attempts=attempts+1, updated_at=? WHERE job_id=?",
                (now, row["job_id"]),
            )
            return Job(
                row["job_id"], row["kind"], json.loads(row["payload"]),
                "running", row["attempts"] + 1,
            )

    def finish(self, job_id: str, success: bool, error: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            self.db.execute(
                "UPDATE jobs SET status=?, updated_at=?, last_error=? WHERE job_id=?",
                ("succeeded" if success else "failed", now, error, job_id),
            )

    def audit(self, event_type: str, actor: str, subject: str, outcome: str, metadata: dict) -> None:
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO audit VALUES (?,?,?,?,?,?,?)",
                (str(uuid4()), event_type, actor, subject, outcome, json.dumps(metadata),
                 datetime.now(timezone.utc).isoformat()),
            )

    def heartbeat(self) -> None:
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO runtime_state VALUES ('heartbeat', ?)",
                (datetime.now(timezone.utc).isoformat(),),
            )

    def status(self) -> dict[str, int | str]:
        with self.lock:
            counts = dict(self.db.execute("SELECT status, COUNT(*) c FROM jobs GROUP BY status").fetchall())
            row = self.db.execute("SELECT value FROM runtime_state WHERE key='heartbeat'").fetchone()
            return {
                "heartbeat": row[0] if row else "never",
                "queued": counts.get("queued", 0),
                "running": counts.get("running", 0),
                "succeeded": counts.get("succeeded", 0),
                "failed": counts.get("failed", 0),
            }


class AurelixRuntime:
    """24/7 orchestration loop with durable state and governed pipeline support."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.store = RuntimeStore(self.config.database_path)
        self.handlers: dict[str, Callable[[dict[str, str]], None]] = {}
        self._stop = threading.Event()
        self.store.recover_running()

    def register(self, kind: str, handler: Callable[[dict[str, str]], None]) -> None:
        if not kind.strip():
            raise ValueError("job kind is required")
        self.handlers[kind] = handler

    def register_pipeline(self, pipeline: GovernedPipeline | None = None, kind: str = "pipeline.run") -> None:
        """Register the real Research→Business governed pipeline as a runtime job."""
        governed = pipeline or GovernedPipeline()

        def handle(payload: dict[str, str]) -> None:
            objective = payload.get("objective", "").strip()
            if not objective:
                raise ValueError("pipeline objective is required")
            governed.run(objective, business_approved=False)

        self.register(kind, handle)

    def submit(self, kind: str, payload: dict[str, str] | None = None) -> str:
        if kind not in self.handlers:
            raise ValueError(f"unregistered job kind: {kind}")
        job_id = self.store.enqueue(kind, payload or {})
        self.store.audit("job.queued", "runtime", job_id, "queued", {"kind": kind})
        return job_id

    def run_once(self) -> bool:
        self.store.heartbeat()
        job = self.store.claim(self.config.max_attempts)
        if not job:
            return False
        try:
            self.handlers[job.kind](job.payload)
            self.store.finish(job.job_id, True)
            self.store.audit("job.completed", "runtime", job.job_id, "succeeded", {"kind": job.kind})
        except Exception as exc:
            self.store.finish(job.job_id, False, str(exc))
            self.store.audit(
                "job.failed", "runtime", job.job_id, "failed",
                {"kind": job.kind, "error": str(exc), "attempt": job.attempts},
            )
        return True

    def serve_forever(self) -> None:
        while not self._stop.is_set():
            worked = self.run_once()
            if not worked:
                self._stop.wait(self.config.worker_poll_seconds)

    def stop(self) -> None:
        self._stop.set()

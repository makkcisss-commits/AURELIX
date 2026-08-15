from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .experiment_runner import ExperimentRunner
from .integrated_engines import Experiment
from .pipeline_runner import GovernedPipeline
from aurelix_core.evaluation import EvaluationEngine


@dataclass(frozen=True)
class RuntimeConfig:
    database_path: str = "data/aurelix.db"
    heartbeat_seconds: float = 30.0
    worker_poll_seconds: float = 1.0
    max_attempts: int = 3
    lease_seconds: float = 60.0


@dataclass(frozen=True)
class Job:
    job_id: str
    kind: str
    payload: dict[str, str]
    status: str
    attempts: int


class RuntimeStore:
    """Durable SQLite state for jobs, leases, audit and runtime heartbeat."""

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
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, last_error TEXT,
                worker_id TEXT, lease_until TEXT
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
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY, hypothesis TEXT NOT NULL,
                success_criteria TEXT NOT NULL, status TEXT NOT NULL, result TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL,
                observation TEXT NOT NULL, recorded_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_observations_experiment
                ON observations(experiment_id, recorded_at);
            """)
        self._migrate_jobs()

    def _migrate_jobs(self) -> None:
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(jobs)").fetchall()}
        with self.lock, self.db:
            if "worker_id" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN worker_id TEXT")
            if "lease_until" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN lease_until TEXT")

    def enqueue(self, kind: str, payload: dict[str, str]) -> str:
        job_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (job_id, kind, json.dumps(payload), "queued", 0, now, now, None, None, None),
            )
        return job_id

    def recover_running(self) -> int:
        """Requeue only jobs whose worker lease has actually expired."""
        now = datetime.now(timezone.utc)
        with self.lock, self.db:
            rows = self.db.execute(
                "SELECT job_id FROM jobs WHERE status='running' AND (lease_until IS NULL OR lease_until < ?)",
                (now.isoformat(),),
            ).fetchall()
            if not rows:
                return 0
            self.db.execute(
                "UPDATE jobs SET status='queued', updated_at=?, worker_id=NULL, lease_until=NULL "
                "WHERE status='running' AND (lease_until IS NULL OR lease_until < ?)",
                (now.isoformat(), now.isoformat()),
            )
        return len(rows)

    def claim(self, worker_id: str, max_attempts: int = 3, lease_seconds: float = 60.0) -> Job | None:
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT * FROM jobs WHERE status='queued' AND attempts < ? ORDER BY created_at LIMIT 1",
                (max_attempts,),
            ).fetchone()
            if not row:
                return None
            now = datetime.now(timezone.utc)
            lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
            updated = self.db.execute(
                "UPDATE jobs SET status='running', attempts=attempts+1, updated_at=?, worker_id=?, lease_until=? "
                "WHERE job_id=? AND status='queued'",
                (now.isoformat(), worker_id, lease_until, row["job_id"]),
            )
            if updated.rowcount != 1:
                return None
            return Job(row["job_id"], row["kind"], json.loads(row["payload"]), "running", row["attempts"] + 1)

    def renew_lease(self, job_id: str, worker_id: str, lease_seconds: float) -> bool:
        until = (datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)).isoformat()
        with self.lock, self.db:
            result = self.db.execute(
                "UPDATE jobs SET lease_until=?, updated_at=? WHERE job_id=? AND status='running' AND worker_id=?",
                (until, datetime.now(timezone.utc).isoformat(), job_id, worker_id),
            )
        return result.rowcount == 1

    def finish(self, job_id: str, worker_id: str, success: bool, error: str | None = None, retry: bool = False) -> None:
        now = datetime.now(timezone.utc).isoformat()
        status = "queued" if retry and not success else ("succeeded" if success else "failed")
        with self.lock, self.db:
            self.db.execute(
                "UPDATE jobs SET status=?, updated_at=?, last_error=?, worker_id=NULL, lease_until=NULL "
                "WHERE job_id=? AND status='running' AND worker_id=?",
                (status, now, error, job_id, worker_id),
            )

    def audit(self, event_type: str, actor: str, subject: str, outcome: str, metadata: dict) -> None:
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO audit VALUES (?,?,?,?,?,?,?)",
                (str(uuid4()), event_type, actor, subject, outcome, json.dumps(metadata), datetime.now(timezone.utc).isoformat()),
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
            return {"heartbeat": row[0] if row else "never", "queued": counts.get("queued", 0), "running": counts.get("running", 0), "succeeded": counts.get("succeeded", 0), "failed": counts.get("failed", 0)}

    def audit_summary(self, limit: int = 20) -> dict[str, Any]:
        with self.lock:
            rows = self.db.execute("SELECT event_type, actor, subject, outcome, metadata, created_at FROM audit ORDER BY created_at DESC LIMIT ?", (max(0, limit),)).fetchall()
        return {"recent": [{"event_type": r[0], "actor": r[1], "subject": r[2], "outcome": r[3], "metadata": json.loads(r[4]), "created_at": r[5]} for r in rows]}


class AurelixRuntime:
    """24/7 orchestration loop with durable state, worker leases and governed pipelines."""

    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or RuntimeConfig()
        self.worker_id = str(uuid4())
        self.store = RuntimeStore(self.config.database_path)
        self.handlers: dict[str, Callable[[dict[str, str]], None]] = {}
        self._stop = threading.Event()
        self.store.recover_running()

    def register(self, kind: str, handler: Callable[[dict[str, str]], None]) -> None:
        if not kind.strip():
            raise ValueError("job kind is required")
        self.handlers[kind] = handler

    def register_pipeline(self, pipeline: GovernedPipeline | None = None, kind: str = "pipeline.run") -> None:
        governed = pipeline or GovernedPipeline()
        def handle(payload: dict[str, str]) -> None:
            objective = payload.get("objective", "").strip()
            if not objective:
                raise ValueError("pipeline objective is required")
            governed.run(objective, business_approved=False)
        self.register(kind, handle)

    def register_experiment(self, experiment: Experiment) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.store.lock, self.store.db:
            self.store.db.execute("""INSERT INTO experiments(experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(experiment_id) DO UPDATE SET hypothesis=excluded.hypothesis,
                success_criteria=excluded.success_criteria, status=excluded.status, result=excluded.result, updated_at=excluded.updated_at""",
                (experiment.id, experiment.hypothesis, json.dumps(experiment.success_criteria), experiment.status, json.dumps(experiment.result) if experiment.result is not None else None, now, now))

    def record_observation(self, experiment_id: str, observation: dict[str, Any]) -> str:
        observation_id = str(uuid4())
        with self.store.lock, self.store.db:
            self.store.db.execute("INSERT INTO observations(id,experiment_id,observation,recorded_at) VALUES (?,?,?,?)", (observation_id, experiment_id, json.dumps(observation), datetime.now(timezone.utc).isoformat()))
        return observation_id

    def query_experiment_observations(self, experiment_id: str) -> list[dict[str, Any]]:
        with self.store.lock:
            rows = self.store.db.execute("SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at", (experiment_id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def query_experiments(self, status: str | None = None) -> list[dict[str, Any]]:
        with self.store.lock:
            query = "SELECT experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at FROM experiments"
            rows = self.store.db.execute(query + (" WHERE status=?" if status else "") + " ORDER BY created_at DESC", (status,) if status else ()).fetchall()
        return [{"experiment_id": r[0], "hypothesis": r[1], "success_criteria": json.loads(r[2]), "status": r[3], "result": json.loads(r[4]) if r[4] else None, "created_at": r[5], "updated_at": r[6]} for r in rows]

    def get_experiment(self, experiment_id: str) -> Experiment:
        match = next((item for item in self.query_experiments() if item["experiment_id"] == experiment_id), None)
        if match is None:
            raise KeyError(f"experiment not found: {experiment_id}")
        return Experiment(id=match["experiment_id"], hypothesis=match["hypothesis"], success_criteria=match["success_criteria"], status=match["status"], result=match["result"])

    def create_experiment_runner(self) -> ExperimentRunner:
        def collector(experiment: Experiment) -> list[dict[str, Any]]:
            self.register_experiment(experiment)
            return self.query_experiment_observations(experiment.id)
        def on_complete(experiment: Experiment, _run) -> None:
            self.register_experiment(experiment)
            self.store.audit("experiment.evaluated", "experiment-runner", experiment.id, "succeeded" if experiment.result and experiment.result.get("passed") else "evaluated", experiment.result or {})
        return ExperimentRunner(collector=collector, evaluator=EvaluationEngine(), on_complete=on_complete)

    def submit(self, kind: str, payload: dict[str, str] | None = None) -> str:
        if kind not in self.handlers:
            raise ValueError(f"unregistered job kind: {kind}")
        job_id = self.store.enqueue(kind, payload or {})
        self.store.audit("job.queued", "runtime", job_id, "queued", {"kind": kind})
        return job_id

    def run_once(self) -> bool:
        self.store.heartbeat()
        job = self.store.claim(self.worker_id, self.config.max_attempts, self.config.lease_seconds)
        if not job:
            return False
        try:
            self.handlers[job.kind](job.payload)
            self.store.finish(job.job_id, self.worker_id, True)
            self.store.audit("job.completed", "runtime", job.job_id, "succeeded", {"kind": job.kind})
        except Exception as exc:
            retry = job.attempts < self.config.max_attempts
            self.store.finish(job.job_id, self.worker_id, False, str(exc), retry=retry)
            self.store.audit("job.retry" if retry else "job.failed", "runtime", job.job_id, "queued" if retry else "failed", {"kind": job.kind, "error": str(exc), "attempt": job.attempts})
        return True

    def serve_forever(self) -> None:
        while not self._stop.is_set():
            worked = self.run_once()
            if not worked:
                self._stop.wait(self.config.worker_poll_seconds)

    def stop(self) -> None:
        self._stop.set()

"""Durable execution queue used by the runtime worker."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from .integrated_engines import EngineStore
from .job_runner import JobExecution, PipelineJobRunner
from .persistence import RuntimeStore


@dataclass
class QueuedJob:
    job_id: str
    objective: str
    status: str = "queued"
    attempts: int = 0


class PersistentJobQueue:
    """Worker-facing queue backed by RuntimeStore."""

    def __init__(self, store: RuntimeStore | None = None, engine_store: EngineStore | None = None):
        self.store = store or RuntimeStore()
        self.engine_store = engine_store or EngineStore()
        self.jobs: Dict[str, QueuedJob] = {}
        self._refresh()

    def _refresh(self) -> None:
        with self.store.lock:
            rows = self.store.db.execute("SELECT job_id, payload, status, attempts FROM jobs").fetchall()
        self.jobs = {
            row["job_id"]: QueuedJob(row["job_id"], json.loads(row["payload"]).get("objective", ""), row["status"], row["attempts"])
            for row in rows
        }

    def enqueue(self, job_id: str, objective: str) -> QueuedJob:
        """Atomically enqueue or return an existing execution for a stable ID.

        The lookup and insert happen in one SQLite write transaction so concurrent
        callers cannot both observe a missing execution ID and race into a UNIQUE
        constraint failure. Reusing an ID for a different objective is rejected.
        """
        now = datetime.now(timezone.utc).isoformat()
        payload = {"objective": objective}
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
                created = row is None
                if row is not None:
                    stored_objective = json.loads(row["payload"]).get("objective", "")
                    if stored_objective != objective:
                        raise ValueError(
                            f"execution_id already belongs to a different objective: {job_id}"
                        )
                    queued = QueuedJob(
                        row["job_id"],
                        stored_objective,
                        row["status"],
                        row["attempts"],
                    )
                else:
                    self.store.db.execute(
                        "INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (
                            job_id,
                            "pipeline",
                            json.dumps(payload, sort_keys=True),
                            "queued",
                            0,
                            now,
                            now,
                        ),
                    )
                    queued = QueuedJob(job_id, objective, "queued", 0)
                self.store.db.commit()
            except Exception:
                self.store.db.rollback()
                raise

        self.jobs[queued.job_id] = queued
        if created:
            self.engine_store.record("job.queued", job_id=job_id)
        return queued

    def claim(self, job_id: str) -> QueuedJob:
        job = self.jobs.get(job_id)
        if job is None:
            record = self.store.get(job_id)
            if record is None:
                raise KeyError(f"unknown job: {job_id}")
            job = QueuedJob(record.job_id, record.payload.get("objective", ""), record.status, record.attempts)
        claimed = self.store.claim(job_id)
        if claimed is None:
            raise RuntimeError(f"job is not claimable: {job.status}")
        job.status = claimed.status
        job.attempts = claimed.attempts
        self.jobs[job_id] = job
        self.engine_store.record("job.claimed", job_id=job_id, attempts=claimed.attempts)
        return job

    def recover_running(self) -> int:
        recovered = self.store.recover_running_jobs()
        self._refresh()
        if recovered:
            self.engine_store.record("job.recovery", recovered=recovered)
        return recovered

    def execute(self, job_id: str, runner: PipelineJobRunner | None = None) -> Any:
        existing = self.store.get(job_id)
        if existing is None:
            raise KeyError(f"unknown job: {job_id}")
        if existing.status == "completed":
            durable = self.store.get_result(job_id) or {"status": "completed", "result": {}}
            return JobExecution(job_id, durable.get("status", "completed"), durable.get("result", {}))
        if existing.status == "failed":
            durable = self.store.get_result(job_id) or {"ok": False, "error": "execution failed"}
            return JobExecution(job_id, "failed", durable)

        job = self.claim(job_id)
        runner = runner or PipelineJobRunner()
        try:
            result = runner.execute(job.job_id, job.objective)
            self.store.complete(job.job_id, {"ok": True, "status": result.status, "result": result.result})
            job.status = "completed"
            self.jobs[job_id] = job
            self.engine_store.record("job.result", job_id=job_id, status=result.status)
            return result
        except Exception as exc:
            retry = job.attempts < 3
            self.store.finish(job.job_id, False, str(exc), retry=retry)
            job.status = "queued" if retry else "failed"
            self.jobs[job_id] = job
            self.engine_store.record("job.failed", job_id=job_id, error=type(exc).__name__, retry=retry)
            raise

    def close(self) -> None:
        self.store.close()

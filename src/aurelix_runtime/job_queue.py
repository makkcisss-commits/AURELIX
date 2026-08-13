"""Durable execution queue used by the runtime worker."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from .integrated_engines import EngineStore
from .job_runner import PipelineJobRunner
from .persistence import RuntimeStore


@dataclass
class QueuedJob:
    job_id: str
    objective: str
    status: str = "queued"
    attempts: int = 0


class PersistentJobQueue:
    """Worker-facing queue backed by RuntimeStore.

    ``jobs`` is a compatibility cache; SQLite is the source of truth for
    lifecycle, retries, idempotency and crash recovery.
    """

    def __init__(self, store: RuntimeStore | None = None, engine_store: EngineStore | None = None):
        self.store = store or RuntimeStore()
        self.engine_store = engine_store or EngineStore()
        self.jobs: Dict[str, QueuedJob] = {}
        self._refresh()

    def _refresh(self) -> None:
        with self.store.lock:
            rows = self.store.db.execute("SELECT job_id, payload, status, attempts FROM jobs").fetchall()
        self.jobs = {
            row["job_id"]: QueuedJob(
                row["job_id"], json.loads(row["payload"]).get("objective", ""), row["status"], row["attempts"]
            )
            for row in rows
        }

    def enqueue(self, job_id: str, objective: str) -> QueuedJob:
        job = self.store.enqueue("pipeline", {"objective": objective}, execution_id=job_id)
        queued = QueuedJob(job.job_id, objective, job.status, job.attempts)
        self.jobs[job.job_id] = queued
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

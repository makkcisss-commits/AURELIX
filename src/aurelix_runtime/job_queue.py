"""Persistent job queue bridge for AURELIX."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .job_runner import PipelineJobRunner
from .integrated_engines import EngineStore


@dataclass
class QueuedJob:
    job_id: str
    objective: str
    status: str = "queued"
    attempts: int = 0


class PersistentJobQueue:
    """Small durable queue abstraction over EngineStore.

    A production deployment can replace the backing store with Postgres/Redis
    without changing the worker-facing contract.
    """

    def __init__(self, store: EngineStore | None = None):
        self.store = store or EngineStore()
        self.jobs: Dict[str, QueuedJob] = {}

    def enqueue(self, job_id: str, objective: str) -> QueuedJob:
        if job_id in self.jobs:
            raise ValueError(f"job already exists: {job_id}")
        job = QueuedJob(job_id, objective)
        self.jobs[job_id] = job
        self.store.record("job.queued", job_id=job_id)
        return job

    def claim(self, job_id: str) -> QueuedJob:
        job = self.jobs[job_id]
        if job.status != "queued":
            raise RuntimeError(f"job is not claimable: {job.status}")
        job.status = "running"
        job.attempts += 1
        self.store.record("job.claimed", job_id=job_id, attempts=job.attempts)
        return job

    def recover_running(self) -> int:
        recovered = 0
        for job in self.jobs.values():
            if job.status == "running":
                job.status = "queued"
                recovered += 1
                self.store.record("job.recovered", job_id=job.job_id)
        return recovered

    def execute(self, job_id: str, runner: PipelineJobRunner | None = None) -> Any:
        job = self.claim(job_id)
        runner = runner or PipelineJobRunner(self.store)
        try:
            result = runner.execute(job.job_id, job.objective)
            job.status = result.status
            self.store.record("job.result", job_id=job_id, status=job.status)
            return result
        except Exception as exc:
            job.status = "failed"
            self.store.record("job.failed", job_id=job_id, error=type(exc).__name__)
            raise

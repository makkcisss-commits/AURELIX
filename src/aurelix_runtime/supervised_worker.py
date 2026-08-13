"""Worker loop guarded by durable execution leases."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from uuid import uuid4
from .job_queue import PersistentJobQueue
from .job_runner import PipelineJobRunner
from .persistence import LeaseLostError

@dataclass
class WorkerConfig:
    max_jobs: int = 1
    max_attempts: int = 3

class SupervisedWorker:
    def __init__(self, queue: PersistentJobQueue, config: WorkerConfig | None = None):
        self.queue = queue
        self.config = config or WorkerConfig()
        self.runner = PipelineJobRunner()
        self.worker_id = str(uuid4())
        self.heartbeat_count = 0

    def heartbeat(self) -> None:
        self.heartbeat_count += 1
        self.queue.store.heartbeat_runtime()
        self.queue.engine_store.record("worker.heartbeat", worker_id=self.worker_id, heartbeat=self.heartbeat_count)

    def run_once(self) -> List[str]:
        self.heartbeat(); processed: List[str] = []
        for job in list(self.queue.jobs.values()):
            if len(processed) >= self.config.max_jobs or job.status != "queued" or job.attempts >= self.config.max_attempts: continue
            try:
                claimed = self.queue.store.claim(job.job_id, self.config.max_attempts, self.worker_id)
                if claimed is None: continue
                job.status, job.attempts, job.worker_id, job.lease_token = "running", claimed.attempts, claimed.worker_id, claimed.lease_token
                self.queue.jobs[job.job_id] = job
                result = self.runner.execute(job.job_id, job.objective)
                self.queue.store.complete(job.job_id, {"ok": True, "status": result.status, "result": result.result}, worker_id=job.worker_id, lease_token=job.lease_token)
                job.status = "completed"; self.queue.jobs[job.job_id] = job
            except LeaseLostError as exc:
                self.queue.engine_store.record("job.lease_lost", job_id=job.job_id, error=str(exc))
            except Exception as exc:
                retry = job.attempts < self.config.max_attempts
                try:
                    self.queue.store.finish(job.job_id, False, str(exc), retry=retry, worker_id=job.worker_id, lease_token=job.lease_token)
                    job.status = "queued" if retry else "failed"; self.queue.jobs[job.job_id] = job
                except LeaseLostError as lease_exc:
                    self.queue.engine_store.record("job.lease_lost", job_id=job.job_id, error=str(lease_exc))
            processed.append(job.job_id)
        return processed

    def recover(self, stale_after_seconds: float | None = None) -> int:
        return self.queue.recover_running(stale_after_seconds=stale_after_seconds)

"""Worker loop guarded by durable queue state and retry limits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import uuid4

from .job_queue import PersistentJobQueue
from .job_runner import PipelineJobRunner


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
        self.heartbeat()
        processed: List[str] = []
        for job in list(self.queue.jobs.values()):
            if len(processed) >= self.config.max_jobs:
                break
            if job.status != "queued" or job.attempts >= self.config.max_attempts:
                continue
            try:
                claimed = self.queue.store.claim(job.job_id, self.config.max_attempts, self.worker_id)
                if claimed is None:
                    continue
                job.status = "running"
                job.attempts = claimed.attempts
                self.queue.jobs[job.job_id] = job
                result = self.runner.execute(job.job_id, job.objective)
                self.queue.store.complete(job.job_id, {"ok": True, "status": result.status, "result": result.result})
                job.status = "completed"
                self.queue.jobs[job.job_id] = job
            except Exception as exc:
                retry = job.attempts < self.config.max_attempts
                try:
                    self.queue.store.finish(job.job_id, False, str(exc), retry=retry)
                    job.status = "queued" if retry else "failed"
                    self.queue.jobs[job.job_id] = job
                except RuntimeError:
                    pass
            processed.append(job.job_id)
        return processed

    def recover(self) -> int:
        return self.queue.recover_running()

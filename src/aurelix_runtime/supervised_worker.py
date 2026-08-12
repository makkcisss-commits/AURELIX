"""Worker execution loop guarded by queue state and retry limits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

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
        self.runner = PipelineJobRunner(queue.store)
        self.heartbeat_count = 0

    def heartbeat(self) -> None:
        self.heartbeat_count += 1
        self.queue.store.record("worker.heartbeat", heartbeat=self.heartbeat_count)

    def run_once(self) -> List[str]:
        self.heartbeat()
        processed: List[str] = []
        for job in list(self.queue.jobs.values()):
            if len(processed) >= self.config.max_jobs:
                break
            if job.status != "queued" or job.attempts >= self.config.max_attempts:
                continue
            self.queue.execute(job.job_id, self.runner)
            processed.append(job.job_id)
        return processed

    def recover(self) -> int:
        return self.queue.recover_running()

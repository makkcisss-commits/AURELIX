from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from .job_queue import PersistentJobQueue
from .job_runner import AutonomyJobRunner


@dataclass(frozen=True)
class Schedule:
    name: str
    interval_seconds: float
    job_kind: str
    payload: dict[str, str]


@dataclass(frozen=True)
class SchedulerConfig:
    max_jobs_per_tick: int = 1
    max_attempts: int = 3


class Scheduler:
    """Scheduler feeding the same durable runtime when a Runtime.submit is supplied."""

    APPROVED_JOB_KINDS = frozenset({"research_pipeline", "autonomy.run", "pipeline.run"})

    def __init__(self, submit: Callable[[str, dict[str, str]], str] | None = None,
                 queue: PersistentJobQueue | None = None,
                 config: SchedulerConfig | None = None) -> None:
        self.config = config or SchedulerConfig()
        self.submit = submit or self._submit
        self._runtime = getattr(submit, "__self__", None) if submit is not None else None
        self.queue = queue or (PersistentJobQueue(store=self._runtime.store) if self._runtime is not None and hasattr(self._runtime, "store") else PersistentJobQueue())
        self._uses_default_submit = submit is None
        self.schedules: list[Schedule] = []
        self._stop = threading.Event()

    def _submit(self, job_kind: str, payload: dict[str, str]) -> str:
        if job_kind not in self.APPROVED_JOB_KINDS:
            raise PermissionError(f"job kind not approved: {job_kind}")
        job_id = f"scheduled-{job_kind}-{time.time_ns()}"
        self.queue.enqueue(job_id, payload.get("objective", ""))
        return job_id

    def add(self, schedule: Schedule) -> None:
        if schedule.interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        if self._uses_default_submit and schedule.job_kind not in self.APPROVED_JOB_KINDS:
            raise PermissionError(f"job kind not approved: {schedule.job_kind}")
        self.schedules.append(schedule)

    def tick(self) -> list[str]:
        """Process at most one due job per tick and never double-run a runtime."""
        processed: list[str] = []
        if self._runtime is not None and hasattr(self._runtime, "run_once"):
            if self._runtime.run_once():
                processed.append("runtime")
            return processed
        runner = AutonomyJobRunner(self.queue.store)
        for job in list(self.queue.jobs.values()):
            if len(processed) >= self.config.max_jobs_per_tick:
                break
            if job.status != "queued" or job.attempts >= self.config.max_attempts:
                continue
            self.queue.execute(job.job_id, runner)
            processed.append(job.job_id)
        return processed

    def recover(self) -> int:
        if self._runtime is not None and hasattr(self._runtime, "store"):
            recovered = self._runtime.store.recover_running_jobs(self.config.max_attempts)
            self.queue._refresh()
            return recovered
        return self.queue.recover_running()

    def serve_forever(self) -> None:
        next_run = {s.name: time.monotonic() + s.interval_seconds for s in self.schedules}
        while not self._stop.is_set():
            now = time.monotonic()
            for schedule in self.schedules:
                if now >= next_run[schedule.name]:
                    self.submit(schedule.job_kind, schedule.payload)
                    next_run[schedule.name] = now + schedule.interval_seconds
            self.tick()
            self._stop.wait(0.5)

    def stop(self) -> None:
        self._stop.set()

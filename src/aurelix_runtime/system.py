"""Single-process AURELIX system boundary."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .runtime import AurelixRuntime, RuntimeConfig
from .scheduler import Schedule, Scheduler, SchedulerConfig


@dataclass(frozen=True)
class SystemConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    scheduler: SchedulerConfig = field(default_factory=lambda: SchedulerConfig(max_jobs_per_tick=4, max_attempts=3))
    enable_autonomy: bool = True


class AurelixSystem:
    """Canonical composition root: one store, queue, worker, scheduler and fabric."""

    def __init__(self, config: SystemConfig | None = None) -> None:
        self.config = config or SystemConfig()
        self.runtime = AurelixRuntime(self.config.runtime)
        if self.config.enable_autonomy:
            self.runtime.register_autonomy()
        self.scheduler = Scheduler(submit=self.runtime.submit, config=self.config.scheduler)
        self._stop = threading.Event()
        self._started = False
        self._next_run: dict[str, float] = {}
        self._schedule_lock = threading.RLock()

    @property
    def store(self):
        return self.runtime.store

    @property
    def status(self) -> str:
        return "stopping" if self._stop.is_set() else ("running" if self._started else "stopped")

    def schedule_autonomy(self, name: str, interval_seconds: float, objective: str) -> None:
        if not objective.strip():
            raise ValueError("objective is required")
        schedule = Schedule(name, interval_seconds, "autonomy.run", {"objective": objective})
        with self._schedule_lock:
            self.scheduler.add(schedule)
            self._next_run.setdefault(name, time.monotonic())

    def submit(self, kind: str, payload: dict[str, str] | None = None) -> str:
        return self.runtime.submit(kind, payload or {})

    def _enqueue_due(self) -> int:
        now = time.monotonic()
        count = 0
        with self._schedule_lock:
            for schedule in self.scheduler.schedules:
                if now < self._next_run.get(schedule.name, now):
                    continue
                self.runtime.submit(schedule.job_kind, schedule.payload)
                self._next_run[schedule.name] = now + schedule.interval_seconds
                self.store.record_audit("schedule.enqueued", "scheduler", schedule.name, "queued", {"job_kind": schedule.job_kind})
                count += 1
        return count

    def tick(self) -> list[str]:
        if not self._started:
            raise RuntimeError("system is not started")
        self._enqueue_due()
        return self.scheduler.tick()

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.recover()
        self._stop.clear()
        self._started = True
        self.store.audit("system.started", "system", "system", "running", {})

    def stop(self) -> None:
        if not self._started:
            return
        self._stop.set()
        self.scheduler.stop()
        self.runtime.stop()
        self._started = False
        self.store.audit("system.stopped", "system", "system", "stopped", {})

    def run_forever(self) -> None:
        self.start()
        try:
            while not self._stop.is_set():
                self.tick()
                self._stop.wait(self.config.runtime.worker_poll_seconds)
        finally:
            self.stop()

    def health(self) -> dict[str, Any]:
        return {"status": self.status, "worker_id": self.runtime.worker_id, "store": "shared", "scheduler": "shared-runtime", "autonomy": "registered" if "autonomy.run" in self.runtime.claimed_handlers else "disabled"}

    def close(self) -> None:
        if self._started:
            self.stop()
        self.runtime.close()


__all__ = ["AurelixSystem", "SystemConfig"]

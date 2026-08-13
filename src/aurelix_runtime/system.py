"""Single-process AURELIX system boundary.

This module is the composition root: one durable RuntimeStore, one execution
fabric, one scheduler and one lifecycle. Higher-level services should enter
through this boundary instead of constructing competing queues/runtimes.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

from .runtime import AurelixRuntime, RuntimeConfig
from .scheduler import Schedule, Scheduler, SchedulerConfig


@dataclass(frozen=True)
class SystemConfig:
    runtime: RuntimeConfig = RuntimeConfig()
    scheduler: SchedulerConfig = SchedulerConfig(max_jobs_per_tick=4, max_attempts=3)
    enable_autonomy: bool = True


class AurelixSystem:
    """The canonical AURELIX composition root.

    All scheduled and externally submitted work goes through the same durable
    runtime and therefore the same leases, retries, audit trail and result store.
    """

    def __init__(self, config: SystemConfig | None = None) -> None:
        self.config = config or SystemConfig()
        self.runtime = AurelixRuntime(self.config.runtime)
        if self.config.enable_autonomy:
            self.runtime.register_autonomy()
        self.scheduler = Scheduler(submit=self.runtime.submit, config=self.config.scheduler)
        self._stop = threading.Event()
        self._started = False

    @property
    def store(self):
        return self.runtime.store

    @property
    def status(self) -> str:
        return "stopping" if self._stop.is_set() else ("running" if self._started else "stopped")

    def schedule_autonomy(self, name: str, interval_seconds: float, objective: str) -> None:
        if not objective.strip():
            raise ValueError("objective is required")
        self.scheduler.add(Schedule(name, interval_seconds, "autonomy.run", {"objective": objective}))

    def submit(self, kind: str, payload: dict[str, str] | None = None) -> str:
        return self.runtime.submit(kind, payload or {})

    def tick(self) -> list[str]:
        if not self._started:
            raise RuntimeError("system is not started")
        return self.scheduler.tick()

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.recover()
        self._stop.clear()
        self._started = True
        self.runtime.store.audit("system.started", "system", "system", "running", {})

    def stop(self) -> None:
        if not self._started:
            return
        self._stop.set()
        self.scheduler.stop()
        self.runtime.stop()
        self._started = False
        self.runtime.store.audit("system.stopped", "system", "system", "stopped", {})

    def run_forever(self) -> None:
        """Run schedule cadence and execution through the same scheduler/runtime."""
        self.start()
        try:
            self.scheduler.serve_forever()
        finally:
            self.stop()

    def health(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "worker_id": self.runtime.worker_id,
            "store": "shared",
            "scheduler": "shared-runtime",
            "autonomy": "registered" if "autonomy.run" in self.runtime.claimed_handlers else "disabled",
        }

    def close(self) -> None:
        if self._started:
            self.stop()
        self.runtime.close()


__all__ = ["AurelixSystem", "SystemConfig"]

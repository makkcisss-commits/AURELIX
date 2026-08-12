"""Supervise bounded AURELIX workers with heartbeat, retry and circuit-breaker state."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Callable, Dict, Optional


class WorkerState(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    OPEN = "open"


@dataclass
class WorkerPolicy:
    heartbeat_timeout_seconds: float = 30.0
    max_failures: int = 3
    cooldown_seconds: float = 60.0
    max_retries: int = 2


@dataclass
class WorkerRecord:
    worker_id: str
    policy: WorkerPolicy
    state: WorkerState = WorkerState.STOPPED
    failures: int = 0
    retries: int = 0
    last_heartbeat: float = field(default_factory=monotonic)
    last_error: Optional[str] = None
    opened_at: Optional[float] = None


class WorkerSupervisor:
    """Small, dependency-free supervisor for the AURELIX execution plane.

    It deliberately does not grant permissions or execute arbitrary code. The
    caller supplies bounded worker callbacks and remains responsible for the
    process/container isolation boundary.
    """

    def __init__(self) -> None:
        self.workers: Dict[str, WorkerRecord] = {}

    def register(self, worker_id: str, policy: WorkerPolicy | None = None) -> WorkerRecord:
        if worker_id in self.workers:
            raise ValueError(f"worker already registered: {worker_id}")
        record = WorkerRecord(worker_id=worker_id, policy=policy or WorkerPolicy())
        self.workers[worker_id] = record
        return record

    def start(self, worker_id: str) -> WorkerRecord:
        record = self._get(worker_id)
        if record.state == WorkerState.OPEN:
            raise RuntimeError("worker circuit is open")
        record.state = WorkerState.RUNNING
        record.last_heartbeat = monotonic()
        return record

    def heartbeat(self, worker_id: str) -> None:
        record = self._get(worker_id)
        if record.state not in {WorkerState.RUNNING, WorkerState.DEGRADED}:
            raise RuntimeError("heartbeat rejected for inactive worker")
        record.last_heartbeat = monotonic()
        record.state = WorkerState.RUNNING

    def failure(self, worker_id: str, error: str) -> WorkerRecord:
        record = self._get(worker_id)
        record.failures += 1
        record.last_error = error[:1000]
        if record.failures >= record.policy.max_failures:
            record.state = WorkerState.OPEN
            record.opened_at = monotonic()
        else:
            record.state = WorkerState.DEGRADED
        return record

    def success(self, worker_id: str) -> WorkerRecord:
        record = self._get(worker_id)
        record.failures = 0
        record.retries = 0
        record.last_error = None
        record.state = WorkerState.RUNNING
        record.last_heartbeat = monotonic()
        return record

    def can_retry(self, worker_id: str) -> bool:
        record = self._get(worker_id)
        return record.retries < record.policy.max_retries and record.state != WorkerState.OPEN

    def record_retry(self, worker_id: str) -> None:
        record = self._get(worker_id)
        if not self.can_retry(worker_id):
            raise RuntimeError("retry budget exhausted")
        record.retries += 1

    def health_check(self, worker_id: str, now: float | None = None) -> WorkerState:
        record = self._get(worker_id)
        now = monotonic() if now is None else now
        if record.state == WorkerState.RUNNING and now - record.last_heartbeat > record.policy.heartbeat_timeout_seconds:
            record.state = WorkerState.DEGRADED
        if record.state == WorkerState.OPEN and record.opened_at is not None:
            if now - record.opened_at >= record.policy.cooldown_seconds:
                record.state = WorkerState.DEGRADED
                record.failures = 0
                record.opened_at = None
        return record.state

    def stop(self, worker_id: str) -> WorkerRecord:
        record = self._get(worker_id)
        record.state = WorkerState.STOPPED
        return record

    def _get(self, worker_id: str) -> WorkerRecord:
        try:
            return self.workers[worker_id]
        except KeyError as exc:
            raise KeyError(f"unknown worker: {worker_id}") from exc

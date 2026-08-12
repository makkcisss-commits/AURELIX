from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic
from typing import Callable


class RuntimeState(str, Enum):
    BOOTING = "BOOTING"
    READY = "READY"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RuntimeLimits:
    max_steps: int = 32
    max_retries: int = 3
    max_runtime_seconds: float = 300.0

    def validate(self) -> None:
        if self.max_steps < 1 or self.max_retries < 0 or self.max_runtime_seconds <= 0:
            raise ValueError("invalid runtime limits")


class OperationsController:
    """Small fail-closed lifecycle controller for the AURELIX runtime."""

    def __init__(self, limits: RuntimeLimits | None = None) -> None:
        self.limits = limits or RuntimeLimits()
        self.limits.validate()
        self.state = RuntimeState.BOOTING
        self._started_at: float | None = None

    def ready(self) -> None:
        if self.state not in {RuntimeState.BOOTING, RuntimeState.DEGRADED}:
            raise RuntimeError(f"cannot become READY from {self.state}")
        self.state = RuntimeState.READY

    def start(self) -> None:
        if self.state != RuntimeState.READY:
            raise RuntimeError("runtime must be READY before start")
        self.state = RuntimeState.RUNNING
        self._started_at = monotonic()

    def degrade(self) -> None:
        if self.state == RuntimeState.RUNNING:
            self.state = RuntimeState.DEGRADED

    def stop(self) -> None:
        if self.state in {RuntimeState.STOPPED, RuntimeState.STOPPING}:
            return
        self.state = RuntimeState.STOPPING
        self.state = RuntimeState.STOPPED

    def fail(self) -> None:
        self.state = RuntimeState.FAILED

    def uptime_seconds(self) -> float:
        if self._started_at is None or self.state in {RuntimeState.BOOTING, RuntimeState.READY, RuntimeState.STOPPED}:
            return 0.0
        return max(0.0, monotonic() - self._started_at)


def retry_bounded(action: Callable[[], object], *, max_retries: int) -> object:
    """Retry only a bounded number of times; never retry indefinitely."""
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    last_error: Exception | None = None
    for _ in range(max_retries + 1):
        try:
            return action()
        except Exception as exc:  # noqa: BLE001 - preserve the last failure for the caller
            last_error = exc
    assert last_error is not None
    raise last_error

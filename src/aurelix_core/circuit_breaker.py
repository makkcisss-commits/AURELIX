from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpen(Exception):
    """Raised when execution is blocked by a circuit breaker."""


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0

    def allow(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def require_allowed(self) -> None:
        if not self.allow():
            raise CircuitOpen("execution blocked by circuit breaker")

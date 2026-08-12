"""Execution limits used by the supervised runtime boundary."""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


class ExecutionTimeout(TimeoutError):
    pass


@dataclass(frozen=True)
class ExecutionLimits:
    timeout_seconds: float = 300.0
    max_attempts: int = 3


class DrainController:
    """Allows new work to stop while an active runtime finishes cleanly."""

    def __init__(self) -> None:
        self._draining = threading.Event()

    @property
    def draining(self) -> bool:
        return self._draining.is_set()

    def begin(self) -> None:
        self._draining.set()

    def allow_new_work(self) -> bool:
        return not self.draining


@contextmanager
def execution_deadline(limits: ExecutionLimits) -> Iterator[None]:
    """Cooperative deadline guard.

    Python cannot safely kill arbitrary running threads. Callers must cooperate
    by checking elapsed time; this context therefore measures and reports the
    deadline instead of pretending it can forcibly terminate a task.
    """
    started = time.monotonic()
    yield
    if time.monotonic() - started > limits.timeout_seconds:
        raise ExecutionTimeout(f"execution exceeded {limits.timeout_seconds}s")

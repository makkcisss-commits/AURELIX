from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Schedule:
    name: str
    interval_seconds: float
    job_kind: str
    payload: dict[str, str]


class Scheduler:
    """Small persistent-runtime scheduler; scheduling only enqueues approved job kinds."""

    def __init__(self, submit: Callable[[str, dict[str, str]], str]) -> None:
        self.submit = submit
        self.schedules: list[Schedule] = []
        self._stop = threading.Event()

    def add(self, schedule: Schedule) -> None:
        if schedule.interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        self.schedules.append(schedule)

    def serve_forever(self) -> None:
        next_run = {s.name: time.monotonic() for s in self.schedules}
        while not self._stop.is_set():
            now = time.monotonic()
            for schedule in self.schedules:
                if now >= next_run[schedule.name]:
                    self.submit(schedule.job_kind, schedule.payload)
                    next_run[schedule.name] = now + schedule.interval_seconds
            self._stop.wait(0.5)

    def stop(self) -> None:
        self._stop.set()

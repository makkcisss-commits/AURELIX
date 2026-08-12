"""Health/readiness and lightweight runtime metrics for AURELIX."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RuntimeMetrics:
    ticks: int = 0
    jobs_processed: int = 0
    heartbeats: int = 0
    recoveries: int = 0
    failures: int = 0
    started_at: str | None = None

    def snapshot(self) -> Dict[str, int | str | None]:
        return self.__dict__.copy()


@dataclass
class RuntimeHealth:
    metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)

    def live(self) -> bool:
        return True

    def ready(self, runtime_started: bool) -> bool:
        return runtime_started

    def snapshot(self, runtime_started: bool) -> Dict[str, object]:
        return {
            "live": self.live(),
            "ready": self.ready(runtime_started),
            "time": utc_now(),
            "metrics": self.metrics.snapshot(),
        }

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class HealthSnapshot:
    status: str
    runtime: str
    checked_at: str
    components: dict[str, str]


class HealthRegistry:
    """Small, dependency-free health registry for the control plane."""

    def __init__(self) -> None:
        self._components: dict[str, str] = {}

    def set(self, component: str, status: str) -> None:
        if not component.strip() or not status.strip():
            raise ValueError("component and status are required")
        self._components[component] = status

    def snapshot(self, runtime: str) -> HealthSnapshot:
        overall = "ok" if all(value == "ok" for value in self._components.values()) else "degraded"
        if not self._components:
            overall = "unknown"
        return HealthSnapshot(
            status=overall,
            runtime=runtime,
            checked_at=datetime.now(timezone.utc).isoformat(),
            components=dict(self._components),
        )

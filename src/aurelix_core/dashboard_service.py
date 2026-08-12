from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .system_snapshot import SystemSnapshot


@dataclass(frozen=True)
class DashboardService:
    """Read-only dashboard service with an optional live snapshot provider."""

    snapshot: SystemSnapshot | None = None
    snapshot_provider: Callable[[], dict[str, Any]] | None = None

    def get_snapshot(self) -> dict[str, Any]:
        if self.snapshot_provider:
            return self.snapshot_provider()
        if self.snapshot is None:
            return SystemSnapshot().public()
        return self.snapshot.public()

    def get_health(self) -> dict[str, str]:
        snapshot = self.get_snapshot()
        return {"status": str(snapshot.get("system", "UNKNOWN")).lower()}

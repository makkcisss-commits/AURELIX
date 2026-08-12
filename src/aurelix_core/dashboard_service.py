from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .system_snapshot import SystemSnapshot


@dataclass(frozen=True)
class DashboardService:
    """Read-only dashboard service.

    This service exposes a deliberately narrow read model. It does not expose
    mutation or execution operations.
    """

    snapshot: SystemSnapshot

    def get_snapshot(self) -> dict[str, Any]:
        return self.snapshot.public()

    def get_health(self) -> dict[str, str]:
        return {"status": self.snapshot.system.lower()}

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SystemSnapshot:
    system: str = "HEALTHY"
    governor: str = "OPERATIONAL"
    policy: str = "ACTIVE"
    audit: str = "RECORDING"
    api: str = "PROTECTED"
    execution: str = "GUARDED"
    budget: str = "ACTIVE"
    breaker: str = "READY"

    def public(self) -> dict[str, Any]:
        """Return only intentionally public dashboard state."""
        return asdict(self)

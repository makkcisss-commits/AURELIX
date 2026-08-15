from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SystemSnapshot:
    """Conservative dashboard state.

    A status is never reported as operational merely because the object exists.
    Callers that have verified a component may explicitly provide a stronger state.
    """

    system: str = "UNVERIFIED"
    governor: str = "UNVERIFIED"
    policy: str = "UNVERIFIED"
    audit: str = "UNVERIFIED"
    api: str = "UNVERIFIED"
    execution: str = "UNVERIFIED"
    budget: str = "UNVERIFIED"
    breaker: str = "UNVERIFIED"

    def public(self) -> dict[str, Any]:
        """Return only intentionally public dashboard state."""
        return asdict(self)

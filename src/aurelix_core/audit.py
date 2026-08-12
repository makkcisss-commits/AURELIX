from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    actor_id: str
    subject_id: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["timestamp"] = self.timestamp.isoformat()
        return record


class AuditLog:
    """Thread-safe V1 audit sink for the core boundary.

    Production storage must be a durable, append-only and access-controlled
    backend. This object intentionally exposes no delete or update operation.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = Lock()

    def append(self, event: AuditEvent) -> None:
        with self._lock:
            self._events.append(event)

    def all(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def recent(self, limit: int = 50) -> tuple[AuditEvent, ...]:
        if limit < 1:
            return ()
        with self._lock:
            return tuple(self._events[-limit:])

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


AuditSink = Callable[[str | None, str, dict[str, Any]], None]


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
    """Thread-safe audit boundary with an optional durable append-only sink.

    Production composition can provide a sink directly. When AURELIX_AUDIT_DB
    is configured, the canonical runtime SQLite store is used automatically.
    Sink failures propagate: a protected decision must not be treated as
    successful when its audit trail cannot be durably recorded.
    """

    def __init__(self, sink: AuditSink | None = None) -> None:
        self._events: list[AuditEvent] = []
        self._lock = Lock()
        self._sink = sink
        self._runtime_store = None
        if self._sink is None:
            audit_db = os.getenv("AURELIX_AUDIT_DB")
            if audit_db:
                from aurelix_runtime.persistence import RuntimeStore
                self._runtime_store = RuntimeStore(audit_db)
                self._sink = self._runtime_store.record_audit

    def append(self, event: AuditEvent) -> None:
        with self._lock:
            if self._sink is not None:
                self._sink(
                    event.subject_id,
                    event.event_type,
                    {
                        "event_id": event.event_id,
                        "actor_id": event.actor_id,
                        "subject_id": event.subject_id,
                        "outcome": event.outcome,
                        "metadata": event.metadata,
                        "timestamp": event.timestamp.isoformat(),
                    },
                )
            self._events.append(event)

    def all(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def recent(self, limit: int = 50) -> tuple[AuditEvent, ...]:
        if limit < 1:
            return ()
        with self._lock:
            return tuple(self._events[-limit:])

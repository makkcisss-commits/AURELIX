"""Durable-friendly in-process message fabric with explicit routing metadata.

The fabric is intentionally transport-agnostic: it gives agents a common
contract today and can be backed by the durable queue without changing callers.
It never grants execution authority; messages carry intent and evidence only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

@dataclass(frozen=True)
class AgentMessage:
    topic: str
    sender: str
    payload: dict[str, Any]
    recipient: str | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    message_id: str = field(default_factory=lambda: str(uuid4()))
    priority: int = 50
    idempotency_key: str | None = None
    security_context: dict[str, Any] = field(default_factory=dict)
    policy_context: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MessageFabric:
    """Deterministic topic router; handlers communicate through one contract."""
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[AgentMessage], Any]]] = {}
        self._seen: set[str] = set()

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], Any]) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def publish(self, message: AgentMessage) -> list[Any]:
        key = message.idempotency_key or message.message_id
        if key in self._seen:
            return []
        self._seen.add(key)
        results: list[Any] = []
        for handler in self._handlers.get(message.topic, []):
            results.append(handler(message))
        return results

    @property
    def topics(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

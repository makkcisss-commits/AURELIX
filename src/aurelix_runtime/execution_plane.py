from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Callable


class ExecutionDenied(PermissionError):
    pass


class ExecutionLimitExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionScope:
    agent_id: str
    allowed_engines: frozenset[str]
    max_steps: int = 1
    max_runtime_seconds: float = 30.0
    environment: str = "sandbox"

    def permits(self, engine: str) -> bool:
        return engine in self.allowed_engines


@dataclass
class ExecutionReceipt:
    agent_id: str
    engine: str
    environment: str
    status: str
    elapsed_seconds: float
    output: dict[str, Any] = field(default_factory=dict)


class ExecutionPlane:
    """Fail-closed execution boundary between orchestration and engine handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, engine: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if not engine or engine in self._handlers:
            raise ValueError("engine must be unique and non-empty")
        self._handlers[engine] = handler

    def execute(self, scope: ExecutionScope, engine: str, payload: dict[str, Any]) -> ExecutionReceipt:
        if not scope.agent_id.strip():
            raise ExecutionDenied("agent identity is required")
        if scope.max_steps < 1 or scope.max_runtime_seconds <= 0:
            raise ExecutionDenied("invalid execution scope")
        if not scope.permits(engine):
            raise ExecutionDenied(f"engine not permitted for agent: {engine}")
        handler = self._handlers.get(engine)
        if handler is None:
            raise ExecutionDenied(f"engine is not registered: {engine}")

        started = monotonic()
        output = handler(dict(payload))
        elapsed = monotonic() - started
        if elapsed > scope.max_runtime_seconds:
            raise ExecutionLimitExceeded(f"execution exceeded {scope.max_runtime_seconds}s")
        if not isinstance(output, dict):
            raise TypeError("engine output must be a dictionary")
        return ExecutionReceipt(scope.agent_id, engine, scope.environment, "completed", elapsed, output)

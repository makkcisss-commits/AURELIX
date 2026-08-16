from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Callable
import threading


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
    execution_id: str | None = None

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
    steps_used: int = 1


class ExecutionPlane:
    """Fail-closed execution boundary between orchestration and engine handlers.

    A multi-step budget is tied to an explicit execution_id. A scope without an
    execution_id is deliberately limited to one step so callers cannot reuse a
    scope object indefinitely while claiming to have a finite multi-step budget.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._step_counts: dict[tuple[str, str, str], int] = {}
        self._lock = threading.RLock()

    def register(self, engine: str, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if not engine or engine in self._handlers:
            raise ValueError("engine must be unique and non-empty")
        self._handlers[engine] = handler

    def reset_execution(self, execution_id: str, agent_id: str | None = None, environment: str | None = None) -> None:
        """Release step accounting after an execution reaches its terminal state."""
        if not execution_id.strip():
            raise ValueError("execution_id is required")
        with self._lock:
            keys = [
                key for key in self._step_counts
                if key[0] == execution_id
                and (agent_id is None or key[1] == agent_id)
                and (environment is None or key[2] == environment)
            ]
            for key in keys:
                self._step_counts.pop(key, None)

    def execute(self, scope: ExecutionScope, engine: str, payload: dict[str, Any]) -> ExecutionReceipt:
        if not scope.agent_id.strip():
            raise ExecutionDenied("agent identity is required")
        if scope.max_steps < 1 or scope.max_runtime_seconds <= 0:
            raise ExecutionDenied("invalid execution scope")
        if scope.max_steps > 1 and not scope.execution_id:
            raise ExecutionDenied("execution_id is required for multi-step scope")
        if not scope.permits(engine):
            raise ExecutionDenied(f"engine not permitted for agent: {engine}")
        handler = self._handlers.get(engine)
        if handler is None:
            raise ExecutionDenied(f"engine is not registered: {engine}")

        key = (scope.execution_id or f"single:{id(scope)}", scope.agent_id, scope.environment)
        with self._lock:
            used = self._step_counts.get(key, 0)
            if used >= scope.max_steps:
                raise ExecutionLimitExceeded(f"execution step budget exhausted ({scope.max_steps})")
            self._step_counts[key] = used + 1
            steps_used = used + 1

        started = monotonic()
        try:
            output = handler(dict(payload))
            elapsed = monotonic() - started
            if elapsed > scope.max_runtime_seconds:
                raise ExecutionLimitExceeded(f"execution exceeded {scope.max_runtime_seconds}s")
            if not isinstance(output, dict):
                raise TypeError("engine output must be a dictionary")
            return ExecutionReceipt(scope.agent_id, engine, scope.environment, "completed", elapsed, output, steps_used)
        except Exception:
            # The step was consumed even when the handler fails or times out.
            # This prevents an automatic retry from silently bypassing the budget.
            raise

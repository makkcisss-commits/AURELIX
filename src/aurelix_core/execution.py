from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .circuit_breaker import CircuitBreaker
from .resource_scope import ResourcePermission, ResourceRequest, authorize_resource


class ExecutionDenied(Exception):
    """Raised when a protected execution cannot proceed."""


@dataclass(frozen=True)
class ExecutionRequest:
    actor_id: str
    resource: ResourceRequest
    permission: ResourcePermission


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    output: object


class ExecutionRuntime:
    """Small deterministic execution boundary for the AURELIX core.

    This runtime intentionally does not execute arbitrary shell commands or
    external tools. Callers provide a bounded callable only after the scope
    and circuit-breaker checks pass.
    """

    def __init__(self, breaker: CircuitBreaker | None = None) -> None:
        self.breaker = breaker or CircuitBreaker()

    def execute(
        self,
        request: ExecutionRequest,
        operation: Callable[[], object],
    ) -> ExecutionResult:
        self.breaker.require_allowed()

        try:
            authorize_resource(request.resource, request.permission)
        except Exception as exc:
            raise ExecutionDenied(str(exc)) from exc

        try:
            output = operation()
        except Exception:
            self.breaker.record_failure()
            raise

        self.breaker.record_success()
        return ExecutionResult(success=True, output=output)

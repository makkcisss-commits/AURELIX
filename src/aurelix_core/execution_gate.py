from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateStatus(str, Enum):
    BLOCKED = "BLOCKED"
    READY = "READY"


@dataclass(frozen=True)
class GateResult:
    status: GateStatus
    reason: str


@dataclass(frozen=True)
class ExecutionContext:
    approved: bool
    policy_allowed: bool
    budget_allowed: bool
    breaker_ready: bool
    audit_ready: bool


class ExecutionGate:
    """Final fail-closed boundary before future side effects.

    This component only authorizes a transition to an execution-ready state.
    It never performs network, financial, shell, deployment, or other side
    effects itself.
    """

    def evaluate(self, context: ExecutionContext) -> GateResult:
        checks = (
            (context.approved, "owner approval required"),
            (context.policy_allowed, "policy blocked execution"),
            (context.budget_allowed, "budget blocked execution"),
            (context.breaker_ready, "circuit breaker is not ready"),
            (context.audit_ready, "audit boundary is not ready"),
        )
        for allowed, reason in checks:
            if not allowed:
                return GateResult(GateStatus.BLOCKED, reason)
        return GateResult(GateStatus.READY, "all execution gates passed")

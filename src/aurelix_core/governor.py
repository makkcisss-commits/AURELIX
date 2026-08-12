from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4

from .approvals import OwnerApproval, apply_owner_approval
from .audit import AuditEvent, AuditLog
from .models import Decision, DecisionRequest
from .policy import PolicyEngine


class GovernorRoute(str, Enum):
    POLICY_ALLOWED = "POLICY_ALLOWED"
    OWNER_REQUIRED = "OWNER_REQUIRED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OrchestrationResult:
    request_id: str
    route: GovernorRoute
    reasons: tuple[str, ...]


class Governor:
    """Central decision boundary for AURELIX; never grants payment authority."""

    def __init__(self, policy: PolicyEngine | None = None, audit: AuditLog | None = None) -> None:
        self.policy = policy or PolicyEngine()
        self.audit = audit or AuditLog()

    def evaluate(self, request: DecisionRequest) -> Decision:
        decision = self.policy.evaluate(request)
        self.audit.append(AuditEvent(
            event_type="decision.evaluated", actor_id=request.actor.id,
            subject_id=request.id, outcome=decision.status.value,
            metadata={"action": request.action.value, "allowed": decision.allowed,
                      "requires_owner": decision.requires_owner}))
        return decision

    def authorize_with_owner_approval(self, request: DecisionRequest, approval: OwnerApproval) -> Decision:
        decision = apply_owner_approval(request, approval)
        self.audit.append(AuditEvent(
            event_type="decision.owner_authorized", actor_id=approval.owner_id,
            subject_id=request.id, outcome=decision.status.value,
            metadata={"approval_id": approval.approval_id,
                      "action": request.action.value, "allowed": decision.allowed}))
        return decision

    def route(self, *, source: str, action: str, requires_capital: bool,
              risk: int, production_change: bool) -> OrchestrationResult:
        if not source.strip() or not action.strip():
            raise ValueError("source and action are required")
        if not 0 <= risk <= 10:
            raise ValueError("risk must be between 0 and 10")
        request_id = str(uuid4())
        if risk >= 8:
            return OrchestrationResult(request_id, GovernorRoute.BLOCKED,
                                       ("risk threshold exceeded",))
        reasons: list[str] = []
        if requires_capital:
            reasons.append("capital authorization required")
        if production_change:
            reasons.append("production change requires controlled review")
        if risk >= 5:
            reasons.append("elevated risk requires owner review")
        if reasons:
            return OrchestrationResult(request_id, GovernorRoute.OWNER_REQUIRED, tuple(reasons))
        return OrchestrationResult(request_id, GovernorRoute.POLICY_ALLOWED,
                                   ("policy checks passed; execution remains gated",))

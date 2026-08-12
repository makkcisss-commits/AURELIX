from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class ApprovalClass(str, Enum):
    OBSERVE = "observe"
    ANALYZE = "analyze"
    PROPOSE = "propose"
    MUTATE = "mutate"
    FINANCIAL = "financial"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    action: str
    approval_class: ApprovalClass
    reason: str
    status: str = "pending"


class ApprovalGate:
    """Fail-closed approval boundary for actions with external side effects."""

    def request(self, *, action: str, approval_class: ApprovalClass, reason: str) -> ApprovalRequest:
        if not action.strip() or not reason.strip():
            raise ValueError("action and reason are required")
        return ApprovalRequest(str(uuid4()), action, approval_class, reason)

    def authorize(self, request: ApprovalRequest, *, approved: bool) -> ApprovalRequest:
        return ApprovalRequest(
            request.request_id,
            request.action,
            request.approval_class,
            request.reason,
            "approved" if approved else "rejected",
        )

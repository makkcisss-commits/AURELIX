from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from threading import Lock
from uuid import uuid4

from .approvals import OwnerApproval, apply_owner_approval
from .audit import AuditLog
from .models import DecisionRequest, DecisionStatus


@dataclass(frozen=True)
class PendingApproval:
    request: DecisionRequest
    created_at: datetime


class ApprovalWorkflow:
    """Control-Center workflow around the existing Governor approval domain."""

    def __init__(self, audit: AuditLog) -> None:
        self._audit = audit
        self._pending: dict[str, PendingApproval] = {}
        self._lock = Lock()

    def submit(self, request: DecisionRequest, actor: str = "system") -> PendingApproval:
        item = PendingApproval(request, datetime.now(timezone.utc))
        with self._lock:
            self._pending[request.id] = item
        self._audit.record("approval.requested", actor, "PENDING")
        return item

    def approve(
        self,
        request_id: str,
        *,
        owner_id: str,
        scope: str,
        max_amount: Decimal | None = None,
        expires_at: datetime | None = None,
    ):
        with self._lock:
            item = self._pending.get(request_id)
        if item is None:
            raise KeyError("approval request not found")

        approval = OwnerApproval(
            request_id=request_id,
            owner_id=owner_id,
            scope=scope,
            max_amount=max_amount,
            expires_at=expires_at,
        )
        decision = apply_owner_approval(item.request, approval)
        if decision.status is DecisionStatus.APPROVED:
            with self._lock:
                self._pending.pop(request_id, None)
            self._audit.record("approval.decided", owner_id, "APPROVED")
        else:
            self._audit.record("approval.decided", owner_id, "REJECTED")
        return decision

    def reject(self, request_id: str, *, owner_id: str):
        with self._lock:
            item = self._pending.pop(request_id, None)
        if item is None:
            raise KeyError("approval request not found")
        self._audit.record("approval.decided", owner_id, "REJECTED")
        return {
            "request_id": request_id,
            "status": DecisionStatus.REJECTED,
            "allowed": False,
        }

    def pending(self) -> tuple[PendingApproval, ...]:
        with self._lock:
            return tuple(self._pending.values())

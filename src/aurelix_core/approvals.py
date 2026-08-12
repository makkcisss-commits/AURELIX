from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from .models import ActionClass, Decision, DecisionStatus, DecisionRequest


@dataclass(frozen=True)
class OwnerApproval:
    """An explicit owner authorization for one protected decision.

    This is a domain record, not an authentication mechanism. A future API layer
    must authenticate the owner and create this record only after that check.
    """

    request_id: str
    owner_id: str
    scope: str
    approved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    max_amount: Decimal | None = None
    approval_id: str = field(default_factory=lambda: str(uuid4()))

    def is_valid_for(self, request: DecisionRequest, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if request.id != self.request_id:
            return False
        if self.expires_at is not None and now >= self.expires_at:
            return False
        if request.action is ActionClass.FINANCIAL and self.max_amount is not None:
            raw_amount = request.payload.get("amount")
            if raw_amount is None:
                return False
            try:
                amount = Decimal(str(raw_amount))
            except Exception:
                return False
            if amount < 0 or amount > self.max_amount:
                return False
        return True


def apply_owner_approval(
    request: DecisionRequest,
    approval: OwnerApproval,
    *,
    now: datetime | None = None,
) -> Decision:
    """Convert a protected proposal into an approved decision only if scoped."""
    if not approval.is_valid_for(request, now=now):
        return Decision(
            request_id=request.id,
            status=DecisionStatus.REJECTED,
            allowed=False,
            reason="Owner approval is missing, expired, mismatched, or outside its scope.",
            requires_owner=True,
        )

    return Decision(
        request_id=request.id,
        status=DecisionStatus.APPROVED,
        allowed=True,
        reason="Protected action has an explicit, scoped owner approval.",
        requires_owner=True,
    )

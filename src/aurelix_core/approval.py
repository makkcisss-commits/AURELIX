from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ApprovalDenied(Exception):
    """Raised when an approval is missing, invalid, or no longer usable."""


@dataclass(frozen=True)
class ApprovalRequest:
    id: str
    subject_id: str
    action: str
    requester_id: str
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current >= self.expires_at


@dataclass(frozen=True)
class ApprovalDecision:
    request_id: str
    approver_id: str
    status: ApprovalStatus
    decided_at: datetime
    reason: str


def create_approval_request(
    request_id: str,
    subject_id: str,
    action: str,
    requester_id: str,
    ttl_minutes: int = 30,
    now: datetime | None = None,
) -> ApprovalRequest:
    if ttl_minutes <= 0:
        raise ValueError("approval TTL must be positive")
    current = now or datetime.now(timezone.utc)
    return ApprovalRequest(
        id=request_id,
        subject_id=subject_id,
        action=action,
        requester_id=requester_id,
        created_at=current,
        expires_at=current + timedelta(minutes=ttl_minutes),
    )


def require_approved(
    request: ApprovalRequest,
    decision: ApprovalDecision,
    now: datetime | None = None,
) -> None:
    if request.is_expired(now):
        raise ApprovalDenied("approval request has expired")
    if decision.request_id != request.id:
        raise ApprovalDenied("approval does not match request")
    if decision.status is not ApprovalStatus.APPROVED:
        raise ApprovalDenied("approval is not granted")
    if decision.decided_at > request.expires_at:
        raise ApprovalDenied("approval was decided after request expiry")

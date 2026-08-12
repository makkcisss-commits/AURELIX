from datetime import datetime, timedelta, timezone

import pytest

from aurelix_core.approval import (
    ApprovalDecision,
    ApprovalDenied,
    ApprovalStatus,
    create_approval_request,
    require_approved,
)


def test_matching_unexpired_approval_is_accepted() -> None:
    now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    request = create_approval_request("apr-1", "task-1", "spend", "agent-1", now=now)
    decision = ApprovalDecision("apr-1", "owner", ApprovalStatus.APPROVED, now, "approved")
    require_approved(request, decision, now=now)


def test_rejected_approval_is_denied() -> None:
    now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    request = create_approval_request("apr-2", "task-2", "spend", "agent-1", now=now)
    decision = ApprovalDecision("apr-2", "owner", ApprovalStatus.REJECTED, now, "no")
    with pytest.raises(ApprovalDenied):
        require_approved(request, decision, now=now)


def test_expired_request_is_denied() -> None:
    now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    request = create_approval_request("apr-3", "task-3", "spend", "agent-1", ttl_minutes=1, now=now)
    decision = ApprovalDecision("apr-3", "owner", ApprovalStatus.APPROVED, now, "approved")
    with pytest.raises(ApprovalDenied):
        require_approved(request, decision, now=now + timedelta(minutes=1))


def test_mismatched_request_is_denied() -> None:
    now = datetime(2026, 8, 12, tzinfo=timezone.utc)
    request = create_approval_request("apr-4", "task-4", "spend", "agent-1", now=now)
    decision = ApprovalDecision("other", "owner", ApprovalStatus.APPROVED, now, "approved")
    with pytest.raises(ApprovalDenied):
        require_approved(request, decision, now=now)

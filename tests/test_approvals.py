from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aurelix_core.approvals import OwnerApproval, apply_owner_approval
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionStatus, DecisionRequest


def financial_request(amount: str = "49.00") -> DecisionRequest:
    return DecisionRequest(
        actor=Actor(id="treasury-agent", role="treasury", autonomy=AutonomyLevel.A3),
        action=ActionClass.FINANCIAL,
        reason="Request an API budget.",
        payload={"amount": amount, "currency": "EUR"},
    )


def test_scoped_owner_approval_unlocks_one_request() -> None:
    request = financial_request()
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="API budget for approved research project",
        max_amount=Decimal("50.00"),
    )
    decision = apply_owner_approval(request, approval)
    assert decision.allowed is True
    assert decision.status is DecisionStatus.APPROVED


def test_approval_cannot_be_reused_for_another_request() -> None:
    request = financial_request()
    other = financial_request()
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="one request only",
        max_amount=Decimal("50.00"),
    )
    decision = apply_owner_approval(other, approval)
    assert decision.allowed is False
    assert decision.status is DecisionStatus.REJECTED


def test_approval_cannot_exceed_amount_limit() -> None:
    request = financial_request("51.00")
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="limited budget",
        max_amount=Decimal("50.00"),
    )
    decision = apply_owner_approval(request, approval)
    assert decision.allowed is False


def test_expired_approval_is_rejected() -> None:
    request = financial_request()
    now = datetime.now(timezone.utc)
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="temporary",
        expires_at=now - timedelta(seconds=1),
    )
    decision = apply_owner_approval(request, approval, now=now)
    assert decision.allowed is False

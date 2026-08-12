from decimal import Decimal

from aurelix_core.approvals import OwnerApproval, apply_owner_approval
from aurelix_core.models import ActionClass, Actor, DecisionRequest, DecisionStatus


def make_request(amount: str) -> DecisionRequest:
    return DecisionRequest(
        actor=Actor(id="test", role="tester"),
        action=ActionClass.FINANCIAL,
        reason="test approval",
        payload={"amount": amount},
    )


def test_scoped_owner_approval_allows_matching_financial_request() -> None:
    request = make_request("49.00")
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="financial",
        max_amount=Decimal("50.00"),
    )
    decision = apply_owner_approval(request, approval)
    assert decision.status is DecisionStatus.APPROVED
    assert decision.allowed is True


def test_approval_cannot_authorize_more_than_its_scope() -> None:
    request = make_request("100.00")
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="financial",
        max_amount=Decimal("50.00"),
    )
    decision = apply_owner_approval(request, approval)
    assert decision.status is DecisionStatus.REJECTED
    assert decision.allowed is False

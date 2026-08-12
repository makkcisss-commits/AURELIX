from decimal import Decimal

from aurelix_core.approval_workflow import ApprovalWorkflow
from aurelix_core.audit import AuditLog
from aurelix_core.models import ActionClass, Actor, DecisionRequest, DecisionStatus


def make_request(amount: str = "49") -> DecisionRequest:
    return DecisionRequest(
        actor=Actor(id="test", role="tester"),
        action=ActionClass.FINANCIAL,
        reason="test approval",
        payload={"amount": amount},
    )


def test_submit_then_approve_records_audit_and_removes_pending() -> None:
    audit = AuditLog()
    workflow = ApprovalWorkflow(audit)
    request = make_request()

    workflow.submit(request)
    decision = workflow.approve(
        request.id,
        owner_id="owner",
        scope="treasury",
        max_amount=Decimal("50"),
    )

    assert decision.status is DecisionStatus.APPROVED
    assert decision.allowed is True
    assert workflow.pending() == ()
    assert [event.outcome for event in audit.recent()] == ["PENDING", "APPROVED"]


def test_approval_above_owner_limit_is_rejected_and_audited() -> None:
    audit = AuditLog()
    workflow = ApprovalWorkflow(audit)
    request = make_request("100")
    workflow.submit(request)

    decision = workflow.approve(
        request.id,
        owner_id="owner",
        scope="treasury",
        max_amount=Decimal("50"),
    )

    assert decision.status is DecisionStatus.REJECTED
    assert decision.allowed is False
    assert workflow.pending() != ()
    assert audit.recent()[-1].outcome == "REJECTED"

from decimal import Decimal

from aurelix_core.approvals import OwnerApproval
from aurelix_core.governor import Governor
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionStatus, DecisionRequest


def test_research_is_allowed_at_recommendation_level() -> None:
    actor = Actor(id="research-agent", role="research", autonomy=AutonomyLevel.A1)
    decision = Governor().evaluate(
        DecisionRequest(actor=actor, action=ActionClass.RESEARCH, reason="Investigate a market.")
    )
    assert decision.allowed is True
    assert decision.status is DecisionStatus.APPROVED
    assert decision.requires_owner is False


def test_financial_action_requires_owner() -> None:
    actor = Actor(id="treasury-agent", role="treasury", autonomy=AutonomyLevel.A3)
    decision = Governor().evaluate(
        DecisionRequest(actor=actor, action=ActionClass.FINANCIAL, reason="Request API budget.")
    )
    assert decision.allowed is False
    assert decision.status is DecisionStatus.PROPOSED
    assert decision.requires_owner is True


def test_low_autonomy_cannot_build() -> None:
    actor = Actor(id="observer", role="observer", autonomy=AutonomyLevel.A0)
    decision = Governor().evaluate(
        DecisionRequest(actor=actor, action=ActionClass.BUILD, reason="Create a prototype.")
    )
    assert decision.allowed is False
    assert decision.status is DecisionStatus.REJECTED


def test_governor_can_apply_scoped_owner_approval() -> None:
    actor = Actor(id="treasury-agent", role="treasury", autonomy=AutonomyLevel.A3)
    request = DecisionRequest(
        actor=actor,
        action=ActionClass.FINANCIAL,
        reason="Request API budget.",
        payload={"amount": "49.00", "currency": "EUR"},
    )
    governor = Governor()
    approval = OwnerApproval(
        request_id=request.id,
        owner_id="owner",
        scope="API budget",
        max_amount=Decimal("50.00"),
    )
    decision = governor.authorize_with_owner_approval(request, approval)
    assert decision.allowed is True
    assert decision.status is DecisionStatus.APPROVED
    assert governor.audit.all()[-1].event_type == "decision.owner_authorized"

from dataclasses import replace
from decimal import Decimal

import pytest

from aurelix_core.economic_opportunity_validation import qualify_opportunity
from aurelix_core.evidence import EvidenceRelation, make_evidence
from aurelix_core.governor import GovernorRoute
from aurelix_core.opportunities import OpportunityStage, build_opportunity
from aurelix_core.opportunity_execution_bridge import OpportunityExecutionBridge
from aurelix_core.resource_scope import ResourceKind, ResourcePermission, ScopeDenied


def approved_opportunity(*, risk: int = 1):
    opportunity = build_opportunity(
        title="Validated business opportunity",
        finding_ids=["finding-1"],
        cost_eur=Decimal("10"),
        monthly_revenue_eur=Decimal("300"),
        hours=2,
        complexity=2,
        risk=risk,
        confidence=Decimal("0.9"),
    )
    return replace(opportunity, stage=OpportunityStage.APPROVED)


def qualification_for(opportunity):
    return qualify_opportunity(
        opportunity,
        evidence_by_claim={
            claim: [
                make_evidence(
                    source_ref=f"https://example.test/{claim}",
                    claim=claim,
                    relation=EvidenceRelation.SUPPORTS,
                    quality=Decimal("0.9"),
                )
            ]
            for claim in ("demand", "monetization_path", "source_reality")
        },
    )


def permission_for(opportunity_id: str) -> ResourcePermission:
    return ResourcePermission(
        actor_id="operator",
        resource=ResourceKind.BUSINESS,
        operations=frozenset({"execute"}),
        scope=opportunity_id,
    )


def test_approved_opportunity_runs_through_governor_runtime_and_revenue():
    opportunity = approved_opportunity()
    bridge = OpportunityExecutionBridge()

    result = bridge.execute(
        opportunity,
        actor_id="operator",
        owner_role="owner",
        channel="digital_service",
        permission=permission_for(opportunity.opportunity_id),
        qualification=qualification_for(opportunity),
        operation=lambda: {"status": "completed", "revenue_eur": "25.00"},
    )

    assert result.route is GovernorRoute.POLICY_ALLOWED
    assert result.executed is True
    assert result.execution is not None
    assert result.observed_revenue_eur == Decimal("25.00")
    assert result.revenue_source_id is not None
    assert bridge.revenue.sources[result.revenue_source_id].is_productive is True


def test_governor_blocks_high_risk_before_runtime():
    opportunity = approved_opportunity(risk=8)
    bridge = OpportunityExecutionBridge()
    called = False

    def forbidden_operation():
        nonlocal called
        called = True
        return {"revenue_eur": "100"}

    result = bridge.execute(
        opportunity,
        actor_id="operator",
        owner_role="owner",
        channel="service",
        permission=permission_for(opportunity.opportunity_id),
        qualification=qualification_for(opportunity),
        operation=forbidden_operation,
    )

    assert result.route is GovernorRoute.BLOCKED
    assert result.executed is False
    assert called is False
    assert result.observed_revenue_eur == Decimal("0")
    assert bridge.revenue.sources == {}


def test_resource_scope_still_applies_after_governor_allows():
    opportunity = approved_opportunity()
    bridge = OpportunityExecutionBridge()
    wrong_scope = ResourcePermission(
        actor_id="operator",
        resource=ResourceKind.BUSINESS,
        operations=frozenset({"execute"}),
        scope="another-opportunity",
    )

    with pytest.raises(ScopeDenied):
        bridge.execute(
            opportunity,
            actor_id="operator",
            owner_role="owner",
            channel="service",
            permission=wrong_scope,
            qualification=qualification_for(opportunity),
            operation=lambda: {"revenue_eur": "50"},
        )

    assert bridge.revenue.sources == {}

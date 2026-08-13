from decimal import Decimal

import pytest

from aurelix_core.opportunities import OpportunityStage, build_opportunity
from aurelix_core.opportunity_revenue_bridge import OpportunityRevenueBridge, SourceStage


def approved_opportunity():
    opportunity = build_opportunity(
        title="validated channel",
        finding_ids=["finding-1"],
        cost_eur=Decimal("5"),
        monthly_revenue_eur=Decimal("90"),
        hours=2,
        complexity=2,
        risk=2,
        confidence=Decimal("0.8"),
    )
    return opportunity.__class__(**{**opportunity.__dict__, "stage": OpportunityStage.APPROVED})


def test_admit_creates_accountable_validation_source():
    bridge = OpportunityRevenueBridge()
    source = bridge.admit(approved_opportunity(), owner_role="business", channel="direct")
    assert source.stage is SourceStage.VALIDATING
    assert source.owner_role == "business"
    assert source.expected_daily_eur == Decimal("3")


def test_observed_revenue_activates_source():
    bridge = OpportunityRevenueBridge()
    source = bridge.admit(approved_opportunity(), owner_role="business", channel="direct")
    updated = bridge.record_observation(source.source_id, Decimal("1.25"), external_reference="txn-1")
    assert updated.stage is SourceStage.ACTIVE
    assert updated.observed_daily_eur == Decimal("1.25")
    assert updated.is_productive


def test_replacement_keeps_chain_traceable():
    bridge = OpportunityRevenueBridge()
    old = bridge.admit(approved_opportunity(), owner_role="business", channel="direct")
    bridge.degrade(old.source_id)
    replacement = bridge.admit(approved_opportunity(), owner_role="business", channel="affiliate")
    retired, promoted = bridge.replace(old.source_id, replacement)
    assert retired.stage is SourceStage.REPLACED
    assert promoted.replacement_for == old.source_id


def test_unapproved_opportunity_cannot_be_admitted():
    bridge = OpportunityRevenueBridge()
    opportunity = build_opportunity(
        title="candidate", finding_ids=[], cost_eur=Decimal("0"),
        monthly_revenue_eur=Decimal("10"), hours=1, complexity=1, risk=1,
        confidence=Decimal("0.5"),
    )
    with pytest.raises(ValueError):
        bridge.admit(opportunity, owner_role="business", channel="direct")

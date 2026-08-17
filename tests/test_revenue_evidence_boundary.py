from decimal import Decimal

import pytest

from aurelix_core.economic_opportunity_validation import qualify_opportunity
from aurelix_core.evidence import EvidenceRelation, make_evidence
from aurelix_core.opportunities import OpportunityStage, build_opportunity
from aurelix_core.opportunity_revenue_bridge import OpportunityRevenueBridge


def _opportunity():
    opportunity = build_opportunity(title="validated channel", finding_ids=["finding-1"], cost_eur=Decimal("5"), monthly_revenue_eur=Decimal("90"), hours=2, complexity=2, risk=2, confidence=Decimal("0.8"))
    evidence_by_claim = {claim: [make_evidence(source_ref=ref, claim=claim, relation=EvidenceRelation.SUPPORTS, quality=Decimal("0.9"))] for claim, ref in (("demand", "prospect-1"), ("monetization_path", "offer-1"), ("source_reality", "source-1"))}
    qualification = qualify_opportunity(opportunity, evidence_by_claim=evidence_by_claim)
    return opportunity.__class__(**{**opportunity.__dict__, "stage": OpportunityStage.APPROVED}), qualification


def test_productive_revenue_requires_external_reference():
    bridge = OpportunityRevenueBridge()
    opportunity, qualification = _opportunity()
    source = bridge.admit(opportunity, qualification=qualification, owner_role="business", channel="test")
    with pytest.raises(ValueError, match="externally verifiable"):
        bridge.record_observation(source.source_id, Decimal("1"))


def test_synthetic_observation_never_becomes_productive():
    bridge = OpportunityRevenueBridge()
    opportunity, qualification = _opportunity()
    source = bridge.admit(opportunity, qualification=qualification, owner_role="business", channel="test")
    updated = bridge.record_observation(source.source_id, Decimal("10"), synthetic=True)
    assert updated.is_productive is False
    assert updated.observed_daily_eur == Decimal("0")

from decimal import Decimal

from aurelix_core.economic_opportunity_validation import (
    QualificationStatus,
    qualify_opportunity,
)
from aurelix_core.evidence import EvidenceRelation, make_evidence
from aurelix_core.opportunities import build_opportunity


def opportunity():
    return build_opportunity(
        title="validated channel",
        finding_ids=["finding-1"],
        cost_eur=Decimal("5"),
        monthly_revenue_eur=Decimal("90"),
        hours=2,
        complexity=2,
        risk=2,
        confidence=Decimal("0.8"),
    )


def evidence(claim: str, ref: str, quality: str = "0.9"):
    return make_evidence(
        source_ref=ref,
        claim=claim,
        relation=EvidenceRelation.SUPPORTS,
        quality=Decimal(quality),
    )


def test_three_required_claims_qualify_opportunity():
    result = qualify_opportunity(
        opportunity(),
        evidence_by_claim={
            "demand": [evidence("demand", "prospect-1")],
            "monetization_path": [evidence("monetization_path", "offer-1")],
            "source_reality": [evidence("source_reality", "source-1")],
        },
    )
    assert result.status is QualificationStatus.QUALIFIED
    assert result.is_qualified
    assert result.confidence == Decimal("0.9")


def test_missing_claim_keeps_opportunity_unqualified():
    result = qualify_opportunity(
        opportunity(),
        evidence_by_claim={
            "demand": [evidence("demand", "prospect-1")],
            "monetization_path": [evidence("monetization_path", "offer-1")],
        },
    )
    assert result.status is QualificationStatus.UNQUALIFIED
    assert not result.is_qualified


def test_low_confidence_claim_keeps_opportunity_unqualified():
    result = qualify_opportunity(
        opportunity(),
        evidence_by_claim={
            "demand": [evidence("demand", "prospect-1")],
            "monetization_path": [evidence("monetization_path", "offer-1")],
            "source_reality": [evidence("source_reality", "source-1", "0.4")],
        },
    )
    assert result.status is QualificationStatus.UNQUALIFIED


def test_contradicting_claim_is_not_qualified():
    result = qualify_opportunity(
        opportunity(),
        evidence_by_claim={
            "demand": [evidence("demand", "prospect-1")],
            "monetization_path": [evidence("monetization_path", "offer-1")],
            "source_reality": [
                evidence("source_reality", "source-1"),
                make_evidence(
                    source_ref="counter-source",
                    claim="source_reality",
                    relation=EvidenceRelation.CONTRADICTS,
                    quality=Decimal("0.9"),
                ),
            ],
        },
    )
    assert result.status is QualificationStatus.CONFLICTED
    assert not result.is_qualified

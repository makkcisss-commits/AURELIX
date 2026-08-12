from decimal import Decimal

from aurelix_core.evidence import EvidenceRelation, make_evidence, verify_claim


def test_claim_with_multiple_sources_is_supported() -> None:
    evidence = [
        make_evidence(source_ref="source-a", claim="claim", relation=EvidenceRelation.SUPPORTS, quality=Decimal("0.9")),
        make_evidence(source_ref="source-b", claim="claim", relation=EvidenceRelation.SUPPORTS, quality=Decimal("0.8")),
    ]
    result = verify_claim(claim="claim", evidence=evidence)
    assert result.status == "SUPPORTED"
    assert result.supporting_count == 2


def test_conflicting_evidence_is_not_presented_as_fact() -> None:
    evidence = [
        make_evidence(source_ref="source-a", claim="claim", relation=EvidenceRelation.SUPPORTS, quality=Decimal("0.6")),
        make_evidence(source_ref="source-b", claim="claim", relation=EvidenceRelation.CONTRADICTS, quality=Decimal("0.9")),
    ]
    result = verify_claim(claim="claim", evidence=evidence)
    assert result.status in {"CONFLICTED", "INCONCLUSIVE"}


def test_no_evidence_is_unverified() -> None:
    result = verify_claim(claim="claim", evidence=[])
    assert result.status == "UNVERIFIED"

"""Evidence gate for economic opportunities.

Separates an economic hypothesis from a qualified opportunity. The gate does
not authorize execution and does not claim revenue; it only determines whether
available evidence is strong enough to move an opportunity into the revenue
pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .evidence import Evidence, EvidenceRelation, verify_claim
from .opportunities import Opportunity


class QualificationStatus(str, Enum):
    UNQUALIFIED = "UNQUALIFIED"
    QUALIFIED = "QUALIFIED"
    CONFLICTED = "CONFLICTED"


@dataclass(frozen=True)
class EconomicQualification:
    opportunity_id: str
    status: QualificationStatus
    confidence: Decimal
    claim_statuses: tuple[tuple[str, str], ...]
    evidence_refs: tuple[str, ...]

    @property
    def is_qualified(self) -> bool:
        return self.status is QualificationStatus.QUALIFIED


REQUIRED_CLAIMS = (
    "demand",
    "monetization_path",
    "source_reality",
)


def qualify_opportunity(
    opportunity: Opportunity,
    *,
    evidence_by_claim: dict[str, list[Evidence]],
) -> EconomicQualification:
    """Qualify an opportunity using explicit evidence for all required claims.

    Every required claim must be supported with confidence >= 0.6 and must not
    be contradicted below that threshold. This is a qualification gate only;
    Governor approval remains a separate authority decision.
    """
    results = {
        claim: verify_claim(claim=claim, evidence=evidence_by_claim.get(claim, []))
        for claim in REQUIRED_CLAIMS
    }
    refs = tuple(
        ref
        for result in results.values()
        for ref in result.evidence_refs
    )
    statuses = tuple((claim, results[claim].status) for claim in REQUIRED_CLAIMS)
    confidence = min((results[claim].confidence for claim in REQUIRED_CLAIMS), default=Decimal("0"))

    conflicted = any(
        result.status == "CONFLICTED" for result in results.values()
    )
    qualified = all(
        result.status == "SUPPORTED" and result.confidence >= Decimal("0.6")
        for result in results.values()
    )
    if conflicted:
        status = QualificationStatus.CONFLICTED
    elif qualified:
        status = QualificationStatus.QUALIFIED
    else:
        status = QualificationStatus.UNQUALIFIED

    return EconomicQualification(
        opportunity_id=opportunity.opportunity_id,
        status=status,
        confidence=confidence,
        claim_statuses=statuses,
        evidence_refs=refs,
    )


def evidence_is_execution_safe(evidence: list[Evidence]) -> bool:
    """Return whether evidence contains no direct contradiction.

    This helper is intentionally conservative and is not an authorization
    mechanism. It is useful for execution planning and monitoring.
    """
    return not any(e.relation is EvidenceRelation.CONTRADICTS for e in evidence)

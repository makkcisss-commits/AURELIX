from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class EvidenceRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXT = "CONTEXT"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_ref: str
    claim: str
    relation: EvidenceRelation
    quality: Decimal


@dataclass(frozen=True)
class VerificationResult:
    claim: str
    evidence_refs: tuple[str, ...]
    supporting_count: int
    contradicting_count: int
    confidence: Decimal
    status: str


def verify_claim(*, claim: str, evidence: list[Evidence]) -> VerificationResult:
    if not claim.strip():
        raise ValueError("claim is required")
    if not evidence:
        return VerificationResult(claim, (), 0, 0, Decimal("0"), "UNVERIFIED")
    supporting = [e for e in evidence if e.relation is EvidenceRelation.SUPPORTS]
    contradicting = [e for e in evidence if e.relation is EvidenceRelation.CONTRADICTS]
    support_score = sum((e.quality for e in supporting), Decimal("0"))
    conflict_score = sum((e.quality for e in contradicting), Decimal("0"))
    confidence = max(Decimal("0"), min(Decimal("1"), support_score / Decimal(max(1, len(evidence))) - conflict_score / Decimal(max(1, len(evidence)))))
    if contradicting and confidence < Decimal("0.5"):
        status = "CONFLICTED"
    elif supporting and confidence >= Decimal("0.6"):
        status = "SUPPORTED"
    else:
        status = "INCONCLUSIVE"
    return VerificationResult(claim, tuple(e.evidence_id for e in evidence), len(supporting), len(contradicting), confidence, status)


def make_evidence(*, source_ref: str, claim: str, relation: EvidenceRelation, quality: Decimal) -> Evidence:
    if not source_ref.strip() or not claim.strip():
        raise ValueError("source_ref and claim are required")
    if not Decimal("0") <= quality <= Decimal("1"):
        raise ValueError("quality must be between 0 and 1")
    return Evidence(str(uuid4()), source_ref, claim, relation, quality)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from urllib.parse import urlparse
from uuid import uuid4


class EvidenceKind(str, Enum):
    MARKET_SIGNAL = "MARKET_SIGNAL"
    CUSTOMER_NEED = "CUSTOMER_NEED"
    PARTNER_SIGNAL = "PARTNER_SIGNAL"
    PRICING = "PRICING"
    TRANSACTION = "TRANSACTION"
    OUTCOME = "OUTCOME"


@dataclass(frozen=True)
class OpportunityEvidence:
    evidence_id: str
    opportunity_id: str
    kind: EvidenceKind
    source_url: str
    source_name: str
    observed_at: datetime
    summary: str
    independently_verified: bool = False

    def __post_init__(self) -> None:
        parsed = urlparse(self.source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be a valid http(s) URL")
        if not self.source_name.strip() or not self.summary.strip():
            raise ValueError("source_name and summary are required")
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.observed_at > datetime.now(timezone.utc):
            raise ValueError("observed_at cannot be in the future")


def record_evidence(*, opportunity_id: str, kind: EvidenceKind, source_url: str,
                    source_name: str, summary: str,
                    observed_at: datetime | None = None,
                    independently_verified: bool = False) -> OpportunityEvidence:
    if not opportunity_id.strip():
        raise ValueError("opportunity_id is required")
    return OpportunityEvidence(
        evidence_id=str(uuid4()),
        opportunity_id=opportunity_id,
        kind=kind,
        source_url=source_url,
        source_name=source_name,
        observed_at=observed_at or datetime.now(timezone.utc),
        summary=summary,
        independently_verified=independently_verified,
    )


@dataclass(frozen=True)
class EvidenceQualification:
    opportunity_id: str
    evidence_count: int
    distinct_sources: int
    verified_count: int
    qualified: bool
    reasons: tuple[str, ...]


def qualify_opportunity_evidence(opportunity_id: str,
                                 evidence: list[OpportunityEvidence],
                                 *, min_evidence: int = 2,
                                 min_sources: int = 2,
                                 require_verified: bool = True) -> EvidenceQualification:
    if min_evidence < 1 or min_sources < 1:
        raise ValueError("minimum evidence and source counts must be positive")
    relevant = [item for item in evidence if item.opportunity_id == opportunity_id]
    sources = {item.source_name.strip().lower() for item in relevant}
    verified = sum(1 for item in relevant if item.independently_verified)
    reasons: list[str] = []
    if len(relevant) < min_evidence:
        reasons.append(f"need at least {min_evidence} independent evidence records")
    if len(sources) < min_sources:
        reasons.append(f"need at least {min_sources} distinct sources")
    if require_verified and verified == 0:
        reasons.append("need at least one independently verified record")
    return EvidenceQualification(
        opportunity_id=opportunity_id,
        evidence_count=len(relevant),
        distinct_sources=len(sources),
        verified_count=verified,
        qualified=not reasons,
        reasons=tuple(reasons),
    )

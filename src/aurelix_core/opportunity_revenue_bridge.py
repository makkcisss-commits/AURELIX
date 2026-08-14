"""Bridge qualified opportunities into measurable revenue-source candidates.

An opportunity must first pass the evidence gate. This bridge still does not
authorize execution and never treats an estimate as realized revenue.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from .economic_opportunity_validation import EconomicQualification
from .opportunities import Opportunity, OpportunityStage
from .revenue import RevenueEngine


class SourceStage(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATING = "VALIDATING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    REPLACED = "REPLACED"


@dataclass(frozen=True)
class RevenueSource:
    source_id: str
    opportunity_id: str
    owner_role: str
    channel: str
    stage: SourceStage = SourceStage.CANDIDATE
    expected_daily_eur: Decimal = Decimal("0")
    observed_daily_eur: Decimal = Decimal("0")
    confidence: Decimal = Decimal("0")
    risk: int = 0
    replacement_for: str | None = None

    @property
    def is_productive(self) -> bool:
        return self.stage == SourceStage.ACTIVE and self.observed_daily_eur > 0


class OpportunityRevenueBridge:
    """Turns evidence-qualified opportunities into accountable revenue sources."""

    def __init__(self, revenue: RevenueEngine | None = None) -> None:
        self.revenue = revenue or RevenueEngine()
        self.sources: dict[str, RevenueSource] = {}

    def admit(
        self,
        opportunity: Opportunity,
        *,
        qualification: EconomicQualification,
        owner_role: str,
        channel: str,
    ) -> RevenueSource:
        if opportunity.stage not in {OpportunityStage.APPROVED, OpportunityStage.RECOMMENDED}:
            raise ValueError("opportunity must be recommended or approved before revenue admission")
        if not qualification.is_qualified or qualification.opportunity_id != opportunity.opportunity_id:
            raise ValueError("opportunity must have matching evidence qualification before revenue admission")
        if not owner_role.strip() or not channel.strip():
            raise ValueError("owner_role and channel are required")
        source = RevenueSource(
            source_id=str(uuid4()),
            opportunity_id=opportunity.opportunity_id,
            owner_role=owner_role,
            channel=channel,
            expected_daily_eur=max(Decimal("0"), opportunity.estimated_monthly_revenue_eur / Decimal("30")),
            confidence=min(opportunity.confidence, qualification.confidence),
            risk=opportunity.risk,
            stage=SourceStage.VALIDATING,
        )
        self.sources[source.source_id] = source
        return source

    def record_observation(self, source_id: str, amount_eur: Decimal, *, external_reference: str | None = None) -> RevenueSource:
        source = self.sources[source_id]
        if amount_eur <= 0:
            raise ValueError("observed revenue must be positive")
        self.revenue.record(activity_id=source_id, amount_eur=amount_eur, source=source.channel, external_reference=external_reference)
        observed = self.revenue.total_for_activity(source_id)
        updated = RevenueSource(**{**source.__dict__, "stage": SourceStage.ACTIVE, "observed_daily_eur": observed})
        self.sources[source_id] = updated
        return updated

    def degrade(self, source_id: str) -> RevenueSource:
        source = self.sources[source_id]
        updated = RevenueSource(**{**source.__dict__, "stage": SourceStage.DEGRADED})
        self.sources[source_id] = updated
        return updated

    def replace(self, source_id: str, replacement: RevenueSource) -> tuple[RevenueSource, RevenueSource]:
        old = self.sources[source_id]
        if replacement.source_id == old.source_id:
            raise ValueError("replacement must be a different source")
        retired = RevenueSource(**{**old.__dict__, "stage": SourceStage.REPLACED})
        promoted = RevenueSource(**{**replacement.__dict__, "replacement_for": old.source_id})
        self.sources[old.source_id] = retired
        self.sources[promoted.source_id] = promoted
        return retired, promoted

    def portfolio(self) -> list[RevenueSource]:
        return list(self.sources.values())

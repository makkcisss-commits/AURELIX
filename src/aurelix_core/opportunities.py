from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class OpportunityStage(str, Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATING = "EVALUATING"
    RECOMMENDED = "RECOMMENDED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    title: str
    source_finding_ids: tuple[str, ...]
    cost_eur: Decimal
    estimated_monthly_revenue_eur: Decimal
    hours_to_first_result: Decimal
    complexity: int
    risk: int
    confidence: Decimal
    stage: OpportunityStage = OpportunityStage.DISCOVERED

    @property
    def expected_monthly_net_eur(self) -> Decimal:
        return self.estimated_monthly_revenue_eur - self.cost_eur

    @property
    def score(self) -> Decimal:
        # Transparent V1 score: upside/confidence, discounted by cost, time,
        # complexity and risk. It is a recommendation aid, never authorization.
        value = (self.estimated_monthly_revenue_eur * self.confidence)
        penalty = self.cost_eur + Decimal(str(self.hours_to_first_result)) * Decimal("2")
        penalty += Decimal(self.complexity + self.risk) * Decimal("5")
        return max(Decimal("0"), value - penalty)


def build_opportunity(*, title: str, finding_ids: list[str], cost_eur: Decimal,
                      monthly_revenue_eur: Decimal, hours: Decimal,
                      complexity: int, risk: int, confidence: Decimal) -> Opportunity:
    if cost_eur < 0 or monthly_revenue_eur < 0 or hours < 0:
        raise ValueError("cost, revenue and hours cannot be negative")
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not 0 <= complexity <= 10 or not 0 <= risk <= 10:
        raise ValueError("complexity and risk must be between 0 and 10")
    return Opportunity(str(uuid4()), title, tuple(finding_ids), cost_eur,
                       monthly_revenue_eur, hours, complexity, risk, confidence)

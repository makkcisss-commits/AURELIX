from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class BusinessStage(str, Enum):
    IDEA = "IDEA"
    VALIDATING = "VALIDATING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class BusinessActivity:
    activity_id: str
    name: str
    channel: str
    description: str
    stage: BusinessStage = BusinessStage.IDEA
    monthly_revenue_eur: Decimal = Decimal("0")
    monthly_cost_eur: Decimal = Decimal("0")

    @property
    def monthly_margin_eur(self) -> Decimal:
        return self.monthly_revenue_eur - self.monthly_cost_eur


def create_activity(*, name: str, channel: str, description: str,
                    monthly_revenue_eur: Decimal = Decimal("0"),
                    monthly_cost_eur: Decimal = Decimal("0")) -> BusinessActivity:
    if not name.strip() or not channel.strip() or not description.strip():
        raise ValueError("name, channel and description are required")
    if monthly_revenue_eur < 0 or monthly_cost_eur < 0:
        raise ValueError("revenue and cost cannot be negative")
    return BusinessActivity(
        activity_id=str(uuid4()), name=name, channel=channel,
        description=description, monthly_revenue_eur=monthly_revenue_eur,
        monthly_cost_eur=monthly_cost_eur,
    )

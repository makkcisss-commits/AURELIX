from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4


@dataclass(frozen=True)
class RevenueRecord:
    revenue_id: str
    activity_id: str
    amount_eur: Decimal
    source: str
    external_reference: str | None
    recorded_at: datetime


class RevenueEngine:
    """Records revenue observations; it never initiates transfers or payments."""

    def __init__(self) -> None:
        self._records: dict[str, RevenueRecord] = {}

    def record(self, *, activity_id: str, amount_eur: Decimal, source: str,
               external_reference: str | None = None) -> RevenueRecord:
        if not activity_id.strip() or not source.strip():
            raise ValueError("activity_id and source are required")
        if amount_eur <= 0:
            raise ValueError("revenue amount must be positive")
        item = RevenueRecord(
            revenue_id=str(uuid4()), activity_id=activity_id,
            amount_eur=amount_eur, source=source,
            external_reference=external_reference,
            recorded_at=datetime.now(timezone.utc),
        )
        self._records[item.revenue_id] = item
        return item

    def total_for_activity(self, activity_id: str) -> Decimal:
        return sum((r.amount_eur for r in self._records.values()
                    if r.activity_id == activity_id), Decimal("0"))

    def total_all(self) -> Decimal:
        return sum((r.amount_eur for r in self._records.values()), Decimal("0"))

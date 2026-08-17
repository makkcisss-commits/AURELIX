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
    # Keep the new field after the legacy positional fields so existing callers
    # constructing RevenueRecord positionally remain source-compatible.
    verified_external: bool = False


class RevenueEngine:
    """Record revenue observations without manufacturing productive revenue.

    ``record`` remains an observation API for backwards compatibility. A
    non-empty external reference is the evidence boundary for productive
    economic learning; unreferenced observations remain non-verified.
    """

    def __init__(self) -> None:
        self._records: dict[str, RevenueRecord] = {}
        self._external_index: dict[str, str] = {}

    def record(self, *, activity_id: str, amount_eur: Decimal, source: str,
               external_reference: str | None = None) -> RevenueRecord:
        reference = external_reference.strip() if external_reference else None
        return self._record(
            activity_id=activity_id,
            amount_eur=amount_eur,
            source=source,
            external_reference=reference,
            verified_external=bool(reference),
        )

    def record_verified_external(self, *, activity_id: str, amount_eur: Decimal,
                                 source: str, external_reference: str) -> RevenueRecord:
        """Record externally verifiable revenue exactly once.

        The reference is the idempotency key. Re-delivery of the same evidence
        returns the original record; a reference cannot be rebound to another
        amount/activity/source.
        """
        reference = external_reference.strip()
        if not reference:
            raise ValueError("verified external revenue requires external_reference")
        existing_id = self._external_index.get(reference)
        if existing_id is not None:
            existing = self._records[existing_id]
            candidate = (activity_id, Decimal(amount_eur), source)
            current = (existing.activity_id, existing.amount_eur, existing.source)
            if existing.verified_external and current == candidate:
                return existing
            raise ValueError("external_reference already maps to a different revenue observation")
        return self._record(
            activity_id=activity_id,
            amount_eur=amount_eur,
            source=source,
            external_reference=reference,
            verified_external=True,
        )

    def _record(self, *, activity_id: str, amount_eur: Decimal, source: str,
                external_reference: str | None, verified_external: bool) -> RevenueRecord:
        if not activity_id.strip() or not source.strip():
            raise ValueError("activity_id and source are required")
        amount = Decimal(amount_eur)
        if amount <= 0:
            raise ValueError("revenue amount must be positive")
        reference = external_reference.strip() if external_reference else None
        if verified_external and not reference:
            raise ValueError("verified external revenue requires external_reference")
        if reference and reference in self._external_index:
            raise ValueError("external_reference already exists")
        item = RevenueRecord(
            revenue_id=str(uuid4()), activity_id=activity_id,
            amount_eur=amount, source=source,
            external_reference=reference,
            verified_external=verified_external,
            recorded_at=datetime.now(timezone.utc),
        )
        self._records[item.revenue_id] = item
        if reference:
            self._external_index[reference] = item.revenue_id
        return item

    def total_for_activity(self, activity_id: str) -> Decimal:
        return sum((r.amount_eur for r in self._records.values()
                    if r.activity_id == activity_id), Decimal("0"))

    def verified_total_for_activity(self, activity_id: str) -> Decimal:
        return sum((r.amount_eur for r in self._records.values()
                    if r.activity_id == activity_id and r.verified_external), Decimal("0"))

    def total_all(self) -> Decimal:
        return sum((r.amount_eur for r in self._records.values()), Decimal("0"))

    def verified_total_all(self) -> Decimal:
        return sum((r.amount_eur for r in self._records.values() if r.verified_external), Decimal("0"))

    def learning_evidence(self) -> list[RevenueRecord]:
        """Return only evidence allowed to enter productive economic learning."""
        return [record for record in self._records.values() if record.verified_external]

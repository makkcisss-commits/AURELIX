"""Additive durable ledger for RevenueEngine observations.

The existing RevenueEngine remains the in-process business API. This adapter adds
restart-safe storage and idempotent ingestion without changing RevenueEngine's
contract or payment behavior.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from threading import RLock

from aurelix_runtime.persistence import RuntimeStore

from .revenue import RevenueEngine, RevenueRecord


class DurableRevenueLedger:
    """Persist revenue observations while delegating business semantics to RevenueEngine."""

    def __init__(self, store: RuntimeStore, revenue: RevenueEngine | None = None) -> None:
        self.store = store
        self.revenue = revenue or RevenueEngine()
        self._lock = RLock()
        with self._lock, self.store.db:
            self.store.db.execute(
                """CREATE TABLE IF NOT EXISTS revenue_records (
                    revenue_id TEXT PRIMARY KEY,
                    activity_id TEXT NOT NULL,
                    amount_eur TEXT NOT NULL,
                    source TEXT NOT NULL,
                    external_reference TEXT,
                    recorded_at TEXT NOT NULL,
                    UNIQUE(activity_id, external_reference)
                )"""
            )
            self.store.db.execute(
                "CREATE INDEX IF NOT EXISTS idx_revenue_activity ON revenue_records(activity_id)"
            )
        self._restore()

    def _restore(self) -> None:
        with self._lock:
            rows = self.store.db.execute(
                "SELECT revenue_id, activity_id, amount_eur, source, external_reference, recorded_at "
                "FROM revenue_records ORDER BY recorded_at, revenue_id"
            ).fetchall()
        for row in rows:
            self.revenue._records[row["revenue_id"]] = RevenueRecord(
                revenue_id=row["revenue_id"],
                activity_id=row["activity_id"],
                amount_eur=Decimal(row["amount_eur"]),
                source=row["source"],
                external_reference=row["external_reference"],
                recorded_at=datetime.fromisoformat(row["recorded_at"]),
            )

    def record(
        self,
        *,
        activity_id: str,
        amount_eur: Decimal,
        source: str,
        external_reference: str | None = None,
    ) -> RevenueRecord:
        """Record once; identical external references are safe to replay."""
        if not activity_id.strip() or not source.strip():
            raise ValueError("activity_id and source are required")
        if amount_eur <= 0:
            raise ValueError("revenue amount must be positive")
        with self._lock, self.store.db:
            if external_reference is not None:
                row = self.store.db.execute(
                    "SELECT revenue_id, activity_id, amount_eur, source, external_reference, recorded_at "
                    "FROM revenue_records WHERE activity_id=? AND external_reference=?",
                    (activity_id, external_reference),
                ).fetchone()
                if row is not None:
                    return self.revenue._records[row["revenue_id"]]
            item = self.revenue.record(
                activity_id=activity_id,
                amount_eur=amount_eur,
                source=source,
                external_reference=external_reference,
            )
            try:
                self.store.db.execute(
                    "INSERT INTO revenue_records(revenue_id,activity_id,amount_eur,source,external_reference,recorded_at) "
                    "VALUES(?,?,?,?,?,?)",
                    (item.revenue_id, item.activity_id, str(item.amount_eur), item.source,
                     item.external_reference, item.recorded_at.astimezone(timezone.utc).isoformat()),
                )
            except Exception:
                self.revenue._records.pop(item.revenue_id, None)
                if external_reference is not None:
                    row = self.store.db.execute(
                        "SELECT revenue_id FROM revenue_records WHERE activity_id=? AND external_reference=?",
                        (activity_id, external_reference),
                    ).fetchone()
                    if row is not None:
                        return self.revenue._records[row["revenue_id"]]
                raise
            return item

    def total_for_activity(self, activity_id: str) -> Decimal:
        return self.revenue.total_for_activity(activity_id)

    def total_all(self) -> Decimal:
        return self.revenue.total_all()

"""Verified attribution of realized economics to accountable opportunities.

This module is intentionally observational: it records provenance for economic
outcomes but never authorizes execution and never treats forecasts as revenue.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class EconomicAttribution:
    opportunity_id: str
    source_id: str
    governor_decision_id: str | None
    resource_scope: str | None
    expected_daily_eur: Decimal
    observed_daily_eur: Decimal
    variance_daily_eur: Decimal
    verified: bool
    external_reference: str

    @property
    def net_daily_eur(self) -> Decimal:
        return self.observed_daily_eur


class EconomicAttributionLedger:
    """Durable, idempotent ledger for verified economic observations.

    With a RuntimeStore, SQLite is the source of truth for cross-process
    uniqueness; the in-memory cache is only an optimization.
    """

    _STATE_KEY = "economic.attribution.ledger"

    def __init__(self, store=None) -> None:
        self.store = store
        self._entries: dict[str, EconomicAttribution] = {}
        self._lock = RLock()
        if self.store is not None:
            self._ensure_durable_schema()
        self._load()

    @staticmethod
    def _from_row(row: Any) -> EconomicAttribution:
        return EconomicAttribution(
            opportunity_id=row["opportunity_id"],
            source_id=row["source_id"],
            governor_decision_id=row["governor_decision_id"],
            resource_scope=row["resource_scope"],
            expected_daily_eur=Decimal(row["expected_daily_eur"]),
            observed_daily_eur=Decimal(row["observed_daily_eur"]),
            variance_daily_eur=Decimal(row["variance_daily_eur"]),
            verified=bool(row["verified"]),
            external_reference=row["external_reference"],
        )

    @staticmethod
    def _payload(entry: EconomicAttribution) -> tuple[Any, ...]:
        return (
            entry.external_reference,
            entry.opportunity_id,
            entry.source_id,
            entry.governor_decision_id,
            entry.resource_scope,
            str(entry.expected_daily_eur),
            str(entry.observed_daily_eur),
            str(entry.variance_daily_eur),
        )

    def _ensure_durable_schema(self) -> None:
        """Create the DB uniqueness boundary and migrate the legacy JSON ledger."""
        with self.store.lock, self.store.db:
            self.store.db.execute(
                """
                CREATE TABLE IF NOT EXISTS economic_attributions (
                    external_reference TEXT PRIMARY KEY,
                    opportunity_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    governor_decision_id TEXT NOT NULL,
                    resource_scope TEXT,
                    expected_daily_eur TEXT NOT NULL,
                    observed_daily_eur TEXT NOT NULL,
                    variance_daily_eur TEXT NOT NULL,
                    verified INTEGER NOT NULL CHECK(verified = 1)
                )
                """
            )
            row = self.store.db.execute(
                "SELECT value FROM runtime_state WHERE key=?", (self._STATE_KEY,)
            ).fetchone()
            if not row:
                return
            try:
                data = json.loads(row[0])
            except (TypeError, json.JSONDecodeError):
                return
            for value in data.values():
                try:
                    if not value.get("verified") or not value.get("governor_decision_id"):
                        continue
                    self.store.db.execute(
                        """
                        INSERT OR IGNORE INTO economic_attributions(
                            external_reference, opportunity_id, source_id,
                            governor_decision_id, resource_scope,
                            expected_daily_eur, observed_daily_eur,
                            variance_daily_eur, verified
                        ) VALUES(?,?,?,?,?,?,?,?,1)
                        """,
                        (
                            value["external_reference"], value["opportunity_id"],
                            value["source_id"], value["governor_decision_id"],
                            value.get("resource_scope"), value["expected_daily_eur"],
                            value["observed_daily_eur"], value["variance_daily_eur"],
                        ),
                    )
                except (KeyError, TypeError, ValueError):
                    continue

    def _load(self) -> None:
        if self.store is None:
            return
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT * FROM economic_attributions ORDER BY external_reference"
            ).fetchall()
        with self._lock:
            self._entries = {row["external_reference"]: self._from_row(row) for row in rows}

    def record(
        self,
        *,
        opportunity_id: str,
        source_id: str,
        expected_daily_eur: Decimal,
        observed_daily_eur: Decimal,
        governor_decision_id: str | None = None,
        resource_scope: str | None = None,
        verified: bool,
        external_reference: str | None = None,
    ) -> EconomicAttribution:
        if not opportunity_id.strip() or not source_id.strip():
            raise ValueError("opportunity_id and source_id are required")
        expected = Decimal(expected_daily_eur)
        observed = Decimal(observed_daily_eur)
        if expected < 0 or observed < 0:
            raise ValueError("economic amounts cannot be negative")
        if not verified:
            raise ValueError("only verified economic observations can be recorded")
        if not governor_decision_id:
            raise ValueError("governor_decision_id is required for attribution")
        if not external_reference or not external_reference.strip():
            raise ValueError("verified economic observations require an external_reference")

        key = external_reference.strip()
        entry = EconomicAttribution(
            opportunity_id=opportunity_id,
            source_id=source_id,
            governor_decision_id=governor_decision_id,
            resource_scope=resource_scope,
            expected_daily_eur=expected,
            observed_daily_eur=observed,
            variance_daily_eur=observed - expected,
            verified=True,
            external_reference=key,
        )

        if self.store is None:
            with self._lock:
                existing = self._entries.get(key)
                if existing is not None:
                    if existing == entry:
                        return existing
                    raise ValueError("external_reference already maps to a different economic observation")
                self._entries[key] = entry
                return entry

        with self._lock, self.store.lock:
            try:
                self.store.db.execute(
                    """
                    INSERT INTO economic_attributions(
                        external_reference, opportunity_id, source_id,
                        governor_decision_id, resource_scope,
                        expected_daily_eur, observed_daily_eur,
                        variance_daily_eur, verified
                    ) VALUES(?,?,?,?,?,?,?,?,1)
                    """,
                    self._payload(entry),
                )
                self.store.db.commit()
            except Exception as exc:
                self.store.db.rollback()
                if exc.__class__.__name__ != "IntegrityError":
                    raise
                row = self.store.db.execute(
                    "SELECT * FROM economic_attributions WHERE external_reference=?", (key,)
                ).fetchone()
                if row is None:
                    raise
                existing = self._from_row(row)
                if existing != entry:
                    raise ValueError("external_reference already maps to a different economic observation")
                self._entries[key] = existing
                return existing
            self._entries[key] = entry
            return entry

    def all(self) -> list[EconomicAttribution]:
        if self.store is not None:
            self._load()
        with self._lock:
            return list(self._entries.values())

    def by_opportunity(self, opportunity_id: str) -> list[EconomicAttribution]:
        return [e for e in self.all() if e.opportunity_id == opportunity_id]

    def learning_evidence(self) -> list[dict[str, Any]]:
        return [
            {
                "opportunity_id": e.opportunity_id,
                "source_id": e.source_id,
                "governor_decision_id": e.governor_decision_id,
                "resource_scope": e.resource_scope,
                "expected_daily_eur": e.expected_daily_eur,
                "observed_daily_eur": e.observed_daily_eur,
                "variance_daily_eur": e.variance_daily_eur,
                "verified": e.verified,
                "external_reference": e.external_reference,
            }
            for e in self.all()
        ]

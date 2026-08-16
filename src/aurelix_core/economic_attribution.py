"""Verified attribution of realized economics to accountable opportunities.

This module is intentionally observational: it records provenance for economic
outcomes but never authorizes execution and never treats forecasts as revenue.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
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
    """Durable, idempotent ledger for verified economic observations."""

    _STATE_KEY = "economic.attribution.ledger"

    def __init__(self, store=None) -> None:
        self.store = store
        self._entries: dict[str, EconomicAttribution] = {}
        self._load()

    def _load(self) -> None:
        if self.store is None:
            return
        with self.store.lock:
            row = self.store.db.execute(
                "SELECT value FROM runtime_state WHERE key=?", (self._STATE_KEY,)
            ).fetchone()
        data = json.loads(row[0]) if row else {}
        self._entries = {
            key: EconomicAttribution(
                opportunity_id=value["opportunity_id"],
                source_id=value["source_id"],
                governor_decision_id=value.get("governor_decision_id"),
                resource_scope=value.get("resource_scope"),
                expected_daily_eur=Decimal(value["expected_daily_eur"]),
                observed_daily_eur=Decimal(value["observed_daily_eur"]),
                variance_daily_eur=Decimal(value["variance_daily_eur"]),
                verified=bool(value["verified"]),
                external_reference=value["external_reference"],
            )
            for key, value in data.items()
        }

    def _persist(self) -> None:
        if self.store is None:
            return
        payload = {
            key: {
                **asdict(entry),
                "expected_daily_eur": str(entry.expected_daily_eur),
                "observed_daily_eur": str(entry.observed_daily_eur),
                "variance_daily_eur": str(entry.variance_daily_eur),
            }
            for key, entry in self._entries.items()
        }
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self._STATE_KEY, json.dumps(payload, sort_keys=True)),
            )

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
        existing = self._entries.get(key)
        if existing is not None:
            if existing == entry:
                return existing
            raise ValueError("external_reference already maps to a different economic observation")
        self._entries[key] = entry
        self._persist()
        return entry

    def all(self) -> list[EconomicAttribution]:
        return list(self._entries.values())

    def by_opportunity(self, opportunity_id: str) -> list[EconomicAttribution]:
        return [e for e in self._entries.values() if e.opportunity_id == opportunity_id]

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
            for e in self._entries.values()
        ]

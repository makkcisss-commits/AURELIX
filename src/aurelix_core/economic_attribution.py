"""Verified attribution of realized economics to accountable opportunities.

This module is intentionally observational: it records provenance for economic
outcomes but never authorizes execution and never treats forecasts as revenue.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    external_reference: str | None = None

    @property
    def net_daily_eur(self) -> Decimal:
        return self.observed_daily_eur


class EconomicAttributionLedger:
    """Stores immutable economic observations with execution provenance."""

    def __init__(self) -> None:
        self._entries: dict[str, EconomicAttribution] = {}

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
        key = external_reference or f"{opportunity_id}:{source_id}"
        existing = self._entries.get(key)
        entry = EconomicAttribution(
            opportunity_id=opportunity_id,
            source_id=source_id,
            governor_decision_id=governor_decision_id,
            resource_scope=resource_scope,
            expected_daily_eur=expected,
            observed_daily_eur=observed,
            variance_daily_eur=observed - expected,
            verified=True,
            external_reference=external_reference,
        )
        if existing is not None and existing == entry:
            return existing
        self._entries[key] = entry
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

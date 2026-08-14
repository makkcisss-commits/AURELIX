"""Convert verified economic attribution into bounded learning signals.

This layer is intentionally observational: it consumes only verified attribution
records, preserves provenance, and never authorizes or triggers execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .economic_attribution import EconomicAttributionLedger


@dataclass(frozen=True)
class VerifiedEconomicLearningSignal:
    opportunity_id: str
    source_id: str
    governor_decision_id: str
    resource_scope: str | None
    expected_daily_eur: Decimal
    observed_daily_eur: Decimal
    variance_daily_eur: Decimal
    external_reference: str | None
    verified: bool = True

    @property
    def realization_ratio(self) -> Decimal:
        if self.expected_daily_eur <= 0:
            return Decimal("0")
        return self.observed_daily_eur / self.expected_daily_eur

    @property
    def evidence_type(self) -> str:
        return "verified_economic_outcome"


class VerifiedEconomicLearning:
    """Expose attribution as idempotent learning evidence, never authority."""

    def __init__(self, ledger: EconomicAttributionLedger) -> None:
        self.ledger = ledger
        self._emitted: set[tuple[Any, ...]] = set()

    def signals(self) -> list[VerifiedEconomicLearningSignal]:
        signals: list[VerifiedEconomicLearningSignal] = []
        for entry in self.ledger.all():
            if not entry.verified or not entry.governor_decision_id:
                continue
            signals.append(
                VerifiedEconomicLearningSignal(
                    opportunity_id=entry.opportunity_id,
                    source_id=entry.source_id,
                    governor_decision_id=entry.governor_decision_id,
                    resource_scope=entry.resource_scope,
                    expected_daily_eur=entry.expected_daily_eur,
                    observed_daily_eur=entry.observed_daily_eur,
                    variance_daily_eur=entry.variance_daily_eur,
                    external_reference=entry.external_reference,
                )
            )
        return signals

    def emit(self) -> list[VerifiedEconomicLearningSignal]:
        """Return only newly observed learning signals; never execute anything."""
        fresh: list[VerifiedEconomicLearningSignal] = []
        for signal in self.signals():
            fingerprint = (
                signal.opportunity_id,
                signal.source_id,
                signal.governor_decision_id,
                signal.resource_scope,
                signal.expected_daily_eur,
                signal.observed_daily_eur,
                signal.variance_daily_eur,
                signal.external_reference,
            )
            if fingerprint in self._emitted:
                continue
            self._emitted.add(fingerprint)
            fresh.append(signal)
        return fresh

    def learning_context(self) -> dict[str, Any]:
        return {
            "evidence_type": "verified_economic_outcome",
            "authority": "none",
            "execution_allowed": False,
            "provenance_required": (
                "opportunity_id, source_id, governor_decision_id, resource_scope"
            ),
            "rule": "only verified realized economics may become learning evidence",
        }

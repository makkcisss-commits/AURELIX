"""Generic value discovery and opportunity evaluation.

The module converts validated intelligence into ranked economic opportunity
candidates. It is proposal-only: Governor remains the authorization boundary
and Runtime remains the execution boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .governor import Governor, GovernorRoute


class ValueModel(str, Enum):
    CONTENT = "content"
    SERVICES = "services"
    PARTNERSHIP = "partnership"
    DIGITAL_PRODUCT = "digital_product"
    LICENSING = "licensing"
    INTERNAL_EFFICIENCY = "internal_efficiency"


@dataclass(frozen=True)
class ValueSignal:
    source_id: str
    capability_id: str
    description: str
    value_model: ValueModel
    expected_value_eur: Decimal
    effort: int
    risk: int
    evidence_strength: int


@dataclass(frozen=True)
class OpportunityEvaluation:
    opportunity_id: str
    source_id: str
    capability_id: str
    value_model: ValueModel
    expected_value_eur: Decimal
    score: Decimal
    governor_route: GovernorRoute
    reasons: tuple[str, ...]
    requires_governor: bool = True


class ValueDiscovery:
    """Rank value signals without granting permission to execute them."""

    def __init__(self, governor: Governor | None = None) -> None:
        self.governor = governor or Governor()
        self._evaluations: dict[str, OpportunityEvaluation] = {}

    def evaluate(self, signal: ValueSignal) -> OpportunityEvaluation:
        self._validate(signal)
        key = self._key(signal)
        existing = self._evaluations.get(key)
        if existing is not None:
            return existing

        score = self._score(signal)
        route = self.governor.route(
            source=signal.source_id,
            action=f"evaluate:{signal.value_model.value}",
            requires_capital=signal.expected_value_eur > Decimal("1000"),
            risk=signal.risk,
            production_change=False,
        )
        evaluation = OpportunityEvaluation(
            opportunity_id=key,
            source_id=signal.source_id,
            capability_id=signal.capability_id,
            value_model=signal.value_model,
            expected_value_eur=signal.expected_value_eur,
            score=score,
            governor_route=route.route,
            reasons=route.reasons,
        )
        self._evaluations[key] = evaluation
        return evaluation

    def rank(self, signals: list[ValueSignal]) -> list[OpportunityEvaluation]:
        evaluations = [self.evaluate(signal) for signal in signals]
        return sorted(evaluations, key=lambda item: item.score, reverse=True)

    @staticmethod
    def _key(signal: ValueSignal) -> str:
        return f"{signal.source_id}:{signal.capability_id}:{signal.value_model.value}"

    @staticmethod
    def _score(signal: ValueSignal) -> Decimal:
        # Bounded, explainable score: value and evidence increase it; effort/risk reduce it.
        value = min(signal.expected_value_eur, Decimal("100000")) / Decimal("100000")
        evidence = Decimal(signal.evidence_strength) / Decimal("10")
        effort = Decimal(signal.effort) / Decimal("10")
        risk = Decimal(signal.risk) / Decimal("10")
        return (value * Decimal("50") + evidence * Decimal("35")
                + (Decimal("1") - effort) * Decimal("10")
                + (Decimal("1") - risk) * Decimal("5")).quantize(Decimal("0.01"))

    @staticmethod
    def _validate(signal: ValueSignal) -> None:
        if not signal.source_id.strip() or not signal.capability_id.strip():
            raise ValueError("source_id and capability_id are required")
        if not signal.description.strip():
            raise ValueError("description is required")
        if signal.expected_value_eur < 0:
            raise ValueError("expected_value_eur cannot be negative")
        if not 1 <= signal.effort <= 10:
            raise ValueError("effort must be between 1 and 10")
        if not 0 <= signal.risk <= 10:
            raise ValueError("risk must be between 0 and 10")
        if not 0 <= signal.evidence_strength <= 10:
            raise ValueError("evidence_strength must be between 0 and 10")

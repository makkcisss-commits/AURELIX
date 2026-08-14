"""Translate validated Academy knowledge into economic value signals.

The adapter is intentionally proposal-only. Academy owns learning and
knowledge; ValueDiscovery owns economic evaluation; Governor remains the
authorization boundary.
"""
from __future__ import annotations

from decimal import Decimal

from .academy import Knowledge
from .value_discovery import ValueModel, ValueSignal


class AcademyValueAdapter:
    """Create normalized value signals from traceable Academy knowledge."""

    def to_signal(
        self,
        knowledge: Knowledge,
        *,
        capability_id: str,
        value_model: ValueModel,
        expected_value_eur: Decimal,
        effort: int,
        risk: int,
    ) -> ValueSignal:
        if not capability_id.strip():
            raise ValueError("capability_id is required")
        if not knowledge.source_refs:
            raise ValueError("knowledge must retain at least one source reference")
        evidence_strength = self._evidence_strength(knowledge.confidence)
        return ValueSignal(
            source_id=knowledge.knowledge_id,
            capability_id=capability_id,
            description=knowledge.summary,
            value_model=value_model,
            expected_value_eur=expected_value_eur,
            effort=effort,
            risk=risk,
            evidence_strength=evidence_strength,
        )

    @staticmethod
    def _evidence_strength(confidence: float) -> int:
        return max(0, min(10, round(confidence * 10)))

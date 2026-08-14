"""Bridge verified economic outcomes into traceable Academy knowledge."""
from __future__ import annotations

from decimal import Decimal

from .academy import AcademyEngine, Knowledge
from .economic_learning_adapter import EconomicLearningAdapter


class EconomicAcademyBridge:
    """Turn verified economic evidence into knowledge, never execution authority."""

    def __init__(self, academy: AcademyEngine, learning: EconomicLearningAdapter) -> None:
        self.academy = academy
        self.learning = learning
        self._published: set[tuple[tuple[str, Decimal, Decimal, bool], ...]] = set()

    def publish(self) -> list[Knowledge]:
        evidence = self.learning.evidence()
        context = self.learning.learning_context()
        if not evidence:
            return []

        signature = tuple(
            sorted(
                (
                    item.source_id,
                    item.observed_daily_eur,
                    item.expected_daily_eur,
                    item.productive,
                )
                for item in evidence
            )
        )
        if signature in self._published:
            return []

        refs = tuple(item.source_id for item in evidence)
        observed = sum((item.observed_daily_eur for item in evidence), start=Decimal("0"))
        expected = sum((item.expected_daily_eur for item in evidence), start=Decimal("0"))
        productive = sum(1 for item in evidence if item.productive)
        confidence = min(1.0, max(0.0, productive / len(evidence)))

        knowledge = self.academy.create_knowledge(
            title="Verified economic outcome",
            summary=(
                f"Observed daily revenue EUR {observed}; expected EUR {expected}; "
                f"productive sources {productive}/{len(evidence)}. "
                f"Evidence type: {context['evidence_type']}."
            ),
            learning_refs=[f"economic:{ref}" for ref in refs],
            source_refs=list(refs),
            confidence=confidence,
        )
        self._published.add(signature)
        return [knowledge]

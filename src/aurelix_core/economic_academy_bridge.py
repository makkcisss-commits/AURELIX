"""Bridge verified economic outcomes into traceable Academy knowledge."""
from __future__ import annotations

from .academy import AcademyEngine, Knowledge
from .economic_learning_adapter import EconomicLearningAdapter


class EconomicAcademyBridge:
    """Turn verified economic evidence into knowledge, never execution authority."""

    def __init__(self, academy: AcademyEngine, learning: EconomicLearningAdapter) -> None:
        self.academy = academy
        self.learning = learning

    def publish(self) -> list[Knowledge]:
        evidence = self.learning.evidence()
        context = self.learning.learning_context()
        if not evidence:
            return []

        refs = tuple(item.source_id for item in evidence)
        observed = sum((item.observed_daily_eur for item in evidence), start=0)
        expected = sum((item.expected_daily_eur for item in evidence), start=0)
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
        return [knowledge]

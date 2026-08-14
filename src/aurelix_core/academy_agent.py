from __future__ import annotations

from dataclasses import dataclass

from .academy import AcademyEngine, Knowledge
from .capability_escalation import CapabilityEscalator, CapabilityGap
from .continuous_intelligence import ContinuousIntelligence, StudyObjective
from .learning import Learning


@dataclass(frozen=True)
class AcademyReview:
    learning_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    synthesis: str
    confidence: float


class AcademyAgent:
    """Turns validated learnings into reusable knowledge and closes capability gaps."""

    def __init__(self, academy: AcademyEngine, intelligence: ContinuousIntelligence | None = None) -> None:
        self.academy = academy
        self.intelligence = intelligence
        self.capability_escalator = CapabilityEscalator(intelligence) if intelligence is not None else None

    def prepare(self, *, learnings: list[Learning], source_refs: list[str],
                synthesis: str, confidence: float) -> AcademyReview:
        if not learnings:
            raise ValueError("academy review requires at least one learning")
        if not synthesis.strip():
            raise ValueError("synthesis is required")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return AcademyReview(
            learning_refs=tuple(item.learning_id for item in learnings),
            source_refs=tuple(source_refs), synthesis=synthesis,
            confidence=confidence,
        )

    def publish(self, *, title: str, review: AcademyReview) -> Knowledge:
        return self.academy.create_knowledge(
            title=title,
            summary=review.synthesis,
            learning_refs=list(review.learning_refs),
            source_refs=list(review.source_refs),
            confidence=review.confidence,
        )

    def escalate_capability(self, *, capability: str, reason: str,
                            requested_by: str, priority: float = 0.8) -> tuple[CapabilityGap, StudyObjective]:
        """Escalate unknown work instead of pretending it is executable."""
        if self.capability_escalator is None:
            raise RuntimeError("capability escalation requires continuous intelligence")
        return self.capability_escalator.escalate(
            capability=capability, reason=reason, requested_by=requested_by,
            priority=priority,
        )

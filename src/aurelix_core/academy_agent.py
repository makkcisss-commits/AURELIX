from __future__ import annotations

from dataclasses import dataclass

from .academy import AcademyEngine, Knowledge
from .learning import Learning


@dataclass(frozen=True)
class AcademyReview:
    learning_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    synthesis: str
    confidence: float


class AcademyAgent:
    """Turns validated learnings into reusable, traceable knowledge."""

    def __init__(self, academy: AcademyEngine) -> None:
        self.academy = academy

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

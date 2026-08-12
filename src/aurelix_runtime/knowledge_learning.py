"""Learning bridge from Academy output into institutional knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List
from uuid import uuid4

from .integrated_engines import AcademyEngine, Evidence, KnowledgeItem
from .knowledge_store import KnowledgeRepository


@dataclass(frozen=True)
class LearningResult:
    knowledge_id: str
    lessons: List[str]
    gaps: List[str]


class KnowledgeLearningService:
    """Persists only lessons supported by verified evidence."""

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
        self.academy = AcademyEngine()

    def learn(self, objective: str, evidence: List[Evidence]) -> LearningResult:
        research = {"objective": objective, "evidence": evidence}
        academy = self.academy.run(research, _AuditOnlyStore())
        lessons = academy["lessons"]
        item = KnowledgeItem(
            id=str(uuid4()),
            title=f"Validated learning: {objective}",
            content="\n".join(lessons),
            evidence=[e for e in evidence if e.verified],
            tags=["academy", "validated"],
        )
        self.repository.put(item)
        return LearningResult(item.id, lessons, academy["gaps"])


class _AuditOnlyStore:
    def record(self, event: str, **data: object) -> None:
        # The outer Runtime owns authoritative audit persistence.
        return None

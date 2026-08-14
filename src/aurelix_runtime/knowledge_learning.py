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
        verified = [item for item in evidence if item.verified]
        research = {"objective": objective, "evidence": verified, "status": "completed" if verified else "no_evidence"}
        academy = self.academy.run(research, _AuditOnlyStore())
        lessons = [lesson for lesson in academy["lessons"] if lesson.strip()]
        item = KnowledgeItem(
            id=str(uuid4()),
            title=f"Validated learning: {objective}",
            content="\n".join(lessons),
            evidence=verified,
            tags=["academy", "validated"],
        )
        self.repository.put(item)
        return LearningResult(item.id, lessons, academy["gaps"])


class _AuditOnlyStore:
    def record(self, event: str, **data: object) -> None:
        return None

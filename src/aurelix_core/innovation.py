from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import uuid4


class InnovationStage(str, Enum):
    PROPOSED = "PROPOSED"
    EVALUATING = "EVALUATING"
    RECOMMENDED = "RECOMMENDED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class InnovationProposal:
    innovation_id: str
    title: str
    knowledge_refs: tuple[str, ...]
    problem: str
    proposed_solution: str
    expected_value: str
    estimated_cost_eur: Decimal
    risk: int
    confidence: Decimal
    stage: InnovationStage = InnovationStage.PROPOSED

    @property
    def priority_score(self) -> Decimal:
        value = self.confidence * Decimal(max(0, 100 - self.risk * 8))
        cost_penalty = min(Decimal("50"), self.estimated_cost_eur)
        return max(Decimal("0"), value - cost_penalty)


def propose_innovation(*, title: str, knowledge_refs: list[str], problem: str,
                       proposed_solution: str, expected_value: str,
                       estimated_cost_eur: Decimal, risk: int,
                       confidence: Decimal) -> InnovationProposal:
    if not title.strip() or not problem.strip() or not proposed_solution.strip():
        raise ValueError("title, problem and proposed solution are required")
    if not knowledge_refs:
        raise ValueError("innovation must reference academy knowledge")
    if estimated_cost_eur < 0:
        raise ValueError("estimated cost cannot be negative")
    if not 0 <= risk <= 10 or not 0 <= confidence <= 1:
        raise ValueError("risk must be 0..10 and confidence must be 0..1")
    return InnovationProposal(
        innovation_id=str(uuid4()), title=title,
        knowledge_refs=tuple(knowledge_refs), problem=problem,
        proposed_solution=proposed_solution, expected_value=expected_value,
        estimated_cost_eur=estimated_cost_eur, risk=risk, confidence=confidence,
    )

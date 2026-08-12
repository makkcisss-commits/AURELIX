"""Promote evaluated experiment outcomes into traceable knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import uuid4

from .integrated_engines import Evidence, KnowledgeItem
from .knowledge_store import KnowledgeRepository


@dataclass(frozen=True)
class ExperimentProvenance:
    experiment_id: str
    evaluation_id: str
    outcome: str
    passed: bool


class ExperimentKnowledgeService:
    """Only evaluated outcomes become durable knowledge candidates."""

    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository

    def record_evaluation(
        self,
        experiment_id: str,
        evaluation_id: str,
        objective: str,
        outcome: str,
        passed: bool,
        evidence: List[Evidence],
    ) -> ExperimentProvenance:
        provenance = ExperimentProvenance(experiment_id, evaluation_id, outcome, passed)
        verified = [item for item in evidence if item.verified]
        if passed and verified:
            item = KnowledgeItem(
                id=str(uuid4()),
                title=f"Experiment result: {objective}",
                content=outcome,
                evidence=verified,
                tags=["experiment", "validated"],
            )
            self.repository.put(item)
        return provenance

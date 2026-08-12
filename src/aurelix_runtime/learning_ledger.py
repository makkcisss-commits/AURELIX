"""Automatic provenance wiring for Academy and Experiment learning."""
from __future__ import annotations

from typing import Iterable

from .provenance import ProvenanceLedger, ProvenanceRecord


class LearningLedger:
    def __init__(self, ledger: ProvenanceLedger | None = None):
        self.ledger = ledger or ProvenanceLedger()

    def record_research(self, research_id: str, evidence_ids: Iterable[str]) -> ProvenanceRecord:
        return self.ledger.append("research", research_id, tuple(evidence_ids))

    def record_evaluation(self, evaluation_id: str, experiment_id: str, evidence_ids: Iterable[str]) -> ProvenanceRecord:
        parents = (experiment_id, *tuple(evidence_ids))
        return self.ledger.append("evaluation", evaluation_id, parents)

    def record_knowledge(self, knowledge_id: str, parent_ids: Iterable[str]) -> ProvenanceRecord:
        return self.ledger.append("knowledge", knowledge_id, tuple(parent_ids))

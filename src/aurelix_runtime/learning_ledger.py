"""Automatic provenance wiring for Academy and Experiment learning."""
from __future__ import annotations

from typing import Iterable, List

from .provenance import ProvenanceLedger, ProvenanceRecord


class LearningLedger:
    def __init__(self, ledger: ProvenanceLedger | None = None):
        self.ledger = ledger or ProvenanceLedger()

    def record_research(self, research_id: str, evidence_ids: Iterable[str]) -> ProvenanceRecord:
        record = ProvenanceRecord(research_id, "research", tuple(evidence_ids))
        self.ledger.record(record)
        return record

    def record_evaluation(self, evaluation_id: str, experiment_id: str, evidence_ids: Iterable[str]) -> ProvenanceRecord:
        parents = (experiment_id, *tuple(evidence_ids))
        record = ProvenanceRecord(evaluation_id, "evaluation", parents)
        self.ledger.record(record)
        return record

    def record_knowledge(self, knowledge_id: str, parent_ids: Iterable[str]) -> ProvenanceRecord:
        record = ProvenanceRecord(knowledge_id, "knowledge", tuple(parent_ids))
        self.ledger.record(record)
        return record

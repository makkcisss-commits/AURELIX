"""Bridge the existing Academy into the generic Continuous Intelligence layer.

The bridge is deliberately one-way in V1: Academy knowledge becomes traceable
CI evidence/knowledge. It does not authorize execution or bypass Governor.
"""
from __future__ import annotations

from dataclasses import dataclass

from .academy import Knowledge
from .continuous_intelligence import (
    ContinuousIntelligence,
    EvidenceKind,
    KnowledgeItem,
    KnowledgeState,
)


@dataclass(frozen=True)
class AcademyKnowledgeProjection:
    knowledge_id: str
    objective_id: str
    evidence_ids: tuple[str, ...]
    domain: str


class AcademyIntelligenceBridge:
    """Projects Academy knowledge into Continuous Intelligence with provenance."""

    def __init__(self, intelligence: ContinuousIntelligence) -> None:
        self.intelligence = intelligence
        self._projections: dict[str, AcademyKnowledgeProjection] = {}

    def project_knowledge(
        self,
        knowledge: Knowledge,
        *,
        domain: str,
        evidence_kind: EvidenceKind = EvidenceKind.SOURCE,
    ) -> tuple[KnowledgeItem, AcademyKnowledgeProjection]:
        if not domain.strip():
            raise ValueError("domain is required")
        if knowledge.knowledge_id in self._projections:
            projection = self._projections[knowledge.knowledge_id]
            return self.intelligence.knowledge[projection.knowledge_id], projection

        self.intelligence.discover_domain(domain)
        objective = self.intelligence.propose_objective(
            domain=domain,
            title=f"Academy knowledge: {knowledge.title}",
            question=knowledge.summary,
            priority=knowledge.confidence,
        )
        references = knowledge.source_refs or knowledge.learning_refs
        if not references:
            raise ValueError("Academy knowledge requires provenance")

        evidence_ids: list[str] = []
        for reference in references:
            evidence = self.intelligence.record_evidence(
                objective_id=objective.objective_id,
                kind=evidence_kind,
                reference=reference,
                strength=knowledge.confidence,
            )
            evidence_ids.append(evidence.evidence_id)

        item = self.intelligence.record_knowledge(
            domain=domain,
            claim=knowledge.summary,
            evidence_refs=tuple(evidence_ids),
            confidence=knowledge.confidence,
            state=KnowledgeState.VALIDATED if knowledge.confidence >= 0.7 else KnowledgeState.CANDIDATE,
        )
        projection = AcademyKnowledgeProjection(
            item.knowledge_id, objective.objective_id, tuple(evidence_ids), domain
        )
        self._projections[knowledge.knowledge_id] = projection
        return item, projection

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
            return self.intelligence.knowledge[knowledge.knowledge_id], projection

        self.intelligence.discover_domain(domain)
        evidence_ids: list[str] = []
        references = knowledge.source_refs or knowledge.learning_refs
        for reference in references:
            evidence = self.intelligence.record_evidence(
                objective_id=self._ensure_objective(domain, knowledge),
                kind=evidence_kind,
                reference=reference,
                strength=knowledge.confidence,
            )
            evidence_ids.append(evidence.evidence_id)

        if not evidence_ids:
            raise ValueError("Academy knowledge requires provenance")

        item = self.intelligence.record_knowledge(
            domain=domain,
            claim=knowledge.summary,
            evidence_refs=tuple(evidence_ids),
            confidence=knowledge.confidence,
            state=KnowledgeState.VALIDATED if knowledge.confidence >= 0.7 else KnowledgeState.CANDIDATE,
        )
        # Preserve Academy identity through the evidence references and projection map.
        projection = AcademyKnowledgeProjection(item.knowledge_id, tuple(evidence_ids), domain)
        self._projections[knowledge.knowledge_id] = projection
        return item, projection

    def _ensure_objective(self, domain: str, knowledge: Knowledge) -> str:
        title = f"Academy knowledge: {knowledge.title}"
        objective = self.intelligence.propose_objective(
            domain=domain,
            title=title,
            question=knowledge.summary,
            priority=knowledge.confidence,
        )
        return objective.objective_id

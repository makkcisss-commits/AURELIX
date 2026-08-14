"""Generic contracts for AURELIX continuous intelligence.

The core is domain-agnostic: new study domains are data, not new engines.
This layer proposes and records learning work; it does not authorize runtime
execution. Authorization remains owned by Governor/Runtime boundaries.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class StudyStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACTIVE = "ACTIVE"
    EVALUATING = "EVALUATING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class EvidenceKind(str, Enum):
    SOURCE = "SOURCE"
    PRACTICE = "PRACTICE"
    EXPERIMENT = "EXPERIMENT"
    BENCHMARK = "BENCHMARK"
    OBSERVATION = "OBSERVATION"
    OUTCOME = "OUTCOME"


class EvaluationStatus(str, Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class KnowledgeState(str, Enum):
    CANDIDATE = "CANDIDATE"
    VALIDATED = "VALIDATED"
    SUPERSEDED = "SUPERSEDED"
    INVALIDATED = "INVALIDATED"


@dataclass(frozen=True)
class StudyObjective:
    objective_id: str
    domain: str
    title: str
    question: str
    target_competencies: tuple[str, ...] = ()
    priority: float = 0.5
    status: StudyStatus = StudyStatus.PROPOSED


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    objective_id: str
    kind: EvidenceKind
    reference: str
    strength: float = 0.5
    notes: str = ""


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    objective_id: str
    hypothesis: str
    method: str
    success_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    objective_id: str
    status: EvaluationStatus = EvaluationStatus.PENDING
    score: float = 0.0
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Capability:
    capability_id: str
    name: str
    domain: str
    required_competencies: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    validated: bool = False


@dataclass(frozen=True)
class KnowledgeItem:
    knowledge_id: str
    domain: str
    claim: str
    state: KnowledgeState = KnowledgeState.CANDIDATE
    confidence: float = 0.0
    evidence_refs: tuple[str, ...] = ()
    supersedes: str | None = None


@dataclass
class ContinuousIntelligence:
    """In-memory V1 coordination registry; no execution or authorization."""

    objectives: dict[str, StudyObjective] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    experiments: dict[str, Experiment] = field(default_factory=dict)
    evaluations: dict[str, Evaluation] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    knowledge: dict[str, KnowledgeItem] = field(default_factory=dict)
    domains: set[str] = field(default_factory=set)

    def discover_domain(self, domain: str) -> str:
        domain = domain.strip()
        if not domain:
            raise ValueError("domain is required")
        self.domains.add(domain)
        return domain

    def propose_objective(self, *, domain: str, title: str, question: str,
                          target_competencies: tuple[str, ...] = (),
                          priority: float = 0.5) -> StudyObjective:
        self.discover_domain(domain)
        if not title.strip() or not question.strip():
            raise ValueError("title and question are required")
        if not 0 <= priority <= 1:
            raise ValueError("priority must be between 0 and 1")
        objective = StudyObjective(str(uuid4()), domain, title, question,
                                   tuple(target_competencies), priority)
        self.objectives[objective.objective_id] = objective
        return objective

    def record_evidence(self, *, objective_id: str, kind: EvidenceKind,
                        reference: str, strength: float = 0.5,
                        notes: str = "") -> Evidence:
        self._require_objective(objective_id)
        if not reference.strip():
            raise ValueError("reference is required")
        if not 0 <= strength <= 1:
            raise ValueError("strength must be between 0 and 1")
        item = Evidence(str(uuid4()), objective_id, kind, reference,
                        strength, notes)
        self.evidence[item.evidence_id] = item
        return item

    def propose_experiment(self, *, objective_id: str, hypothesis: str,
                           method: str, success_criteria: tuple[str, ...] = ()) -> Experiment:
        self._require_objective(objective_id)
        if not hypothesis.strip() or not method.strip():
            raise ValueError("hypothesis and method are required")
        experiment = Experiment(str(uuid4()), objective_id, hypothesis, method,
                                tuple(success_criteria))
        self.experiments[experiment.experiment_id] = experiment
        return experiment

    def evaluate(self, *, objective_id: str, score: float,
                 evidence_refs: tuple[str, ...]) -> Evaluation:
        self._require_objective(objective_id)
        if not 0 <= score <= 1:
            raise ValueError("score must be between 0 and 1")
        for ref in evidence_refs:
            if ref not in self.evidence:
                raise ValueError("evaluation references unknown evidence")
        status = EvaluationStatus.PASSED if score >= 0.7 else EvaluationStatus.FAILED
        evaluation = Evaluation(str(uuid4()), objective_id, status, score,
                                tuple(evidence_refs))
        self.evaluations[evaluation.evaluation_id] = evaluation
        return evaluation

    def validate_capability(self, *, name: str, domain: str,
                            required_competencies: tuple[str, ...],
                            evidence_refs: tuple[str, ...]) -> Capability:
        if not name.strip() or not domain.strip():
            raise ValueError("name and domain are required")
        if not evidence_refs:
            raise ValueError("capability requires evidence")
        for ref in evidence_refs:
            if ref not in self.evidence:
                raise ValueError("capability references unknown evidence")
        capability = Capability(str(uuid4()), name, domain,
                                tuple(required_competencies), tuple(evidence_refs), True)
        self.capabilities[capability.capability_id] = capability
        return capability

    def record_knowledge(self, *, domain: str, claim: str,
                         evidence_refs: tuple[str, ...], confidence: float = 0.5,
                         state: KnowledgeState = KnowledgeState.VALIDATED,
                         supersedes: str | None = None) -> KnowledgeItem:
        self.discover_domain(domain)
        if not claim.strip() or not evidence_refs:
            raise ValueError("claim and evidence are required")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        for ref in evidence_refs:
            if ref not in self.evidence:
                raise ValueError("knowledge references unknown evidence")
        if state == KnowledgeState.SUPERSEDED and not supersedes:
            raise ValueError("superseded knowledge requires a predecessor")
        item = KnowledgeItem(str(uuid4()), domain, claim, state, confidence,
                             tuple(evidence_refs), supersedes)
        self.knowledge[item.knowledge_id] = item
        return item

    def _require_objective(self, objective_id: str) -> None:
        if objective_id not in self.objectives:
            raise KeyError(objective_id)

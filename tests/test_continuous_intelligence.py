import pytest

from aurelix_core.continuous_intelligence import (
    ContinuousIntelligence,
    EvidenceKind,
    EvaluationStatus,
    KnowledgeState,
)


def test_domain_discovery_is_generic_and_extensible():
    intelligence = ContinuousIntelligence()
    domain = intelligence.discover_domain("Astrobiology")
    assert domain == "Astrobiology"
    assert domain in intelligence.domains


def test_study_objective_is_generic_and_domain_agnostic():
    intelligence = ContinuousIntelligence()
    objective = intelligence.propose_objective(
        domain="Engineering",
        title="Validate a new engineering technique",
        question="Does the technique improve the measured outcome?",
    )
    assert objective.domain == "Engineering"
    assert objective.objective_id in intelligence.objectives

    with pytest.raises(ValueError):
        intelligence.propose_objective(domain="Engineering", title="", question="invalid")


def test_evidence_experiment_evaluation_and_capability_form_a_lifecycle():
    intelligence = ContinuousIntelligence()
    objective = intelligence.propose_objective(
        domain="Engineering",
        title="Build and validate a capability",
        question="Can the capability be demonstrated?",
    )
    evidence = intelligence.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="sandbox-result",
        strength=0.9,
    )
    experiment = intelligence.propose_experiment(
        objective_id=objective.objective_id,
        hypothesis="The capability will pass the sandbox criterion",
        method="bounded sandbox",
        success_criteria=("criterion passes",),
    )
    evaluation = intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.85,
        evidence_refs=(evidence.evidence_id,),
    )
    capability = intelligence.validate_capability(
        name="validated-engineering-capability",
        domain="Engineering",
        required_competencies=("engineering",),
        evidence_refs=(evidence.evidence_id,),
    )

    assert experiment.experiment_id in intelligence.experiments
    assert evaluation.status is EvaluationStatus.PASSED
    assert capability.validated is True


def test_knowledge_requires_evidence_and_tracks_validation_state():
    intelligence = ContinuousIntelligence()
    objective = intelligence.propose_objective(
        domain="Science", title="Validate claim", question="Is the claim supported?"
    )
    evidence = intelligence.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.SOURCE,
        reference="trusted-source",
        strength=0.95,
    )
    knowledge = intelligence.record_knowledge(
        domain="Science",
        claim="validated claim",
        evidence_refs=(evidence.evidence_id,),
        confidence=0.9,
        state=KnowledgeState.VALIDATED,
    )
    assert knowledge.state is KnowledgeState.VALIDATED
    assert knowledge.evidence_refs == (evidence.evidence_id,)

    with pytest.raises(ValueError):
        intelligence.record_knowledge(
            domain="Science", claim="invalid", evidence_refs=(), confidence=0.9
        )


def test_capability_requires_evidence():
    intelligence = ContinuousIntelligence()
    with pytest.raises(ValueError):
        intelligence.validate_capability(
            name="unproven",
            domain="Science",
            required_competencies=(),
            evidence_refs=(),
        )

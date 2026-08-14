import pytest

from aurelix_core.continuous_intelligence import (
    Capability,
    ContinuousIntelligence,
    Evidence,
    Evaluation,
    Experiment,
    KnowledgeState,
    StudyObjective,
)


def test_domain_discovery_is_generic_and_extensible():
    intelligence = ContinuousIntelligence()
    domain = intelligence.discover_domain("Astrobiology")

    assert domain.name == "Astrobiology"
    assert domain.domain_id in intelligence.domains


def test_study_requires_a_known_domain_and_objective():
    intelligence = ContinuousIntelligence()
    intelligence.discover_domain("Engineering")

    objective = StudyObjective(
        objective_id="obj-1",
        domain_id=next(iter(intelligence.domains)),
        description="Validate a new engineering technique",
    )
    intelligence.add_objective(objective)

    assert intelligence.objectives["obj-1"] == objective

    with pytest.raises(ValueError):
        intelligence.add_objective(
            StudyObjective("obj-2", "missing-domain", "invalid")
        )


def test_evidence_experiment_evaluation_and_capability_form_a_lifecycle():
    intelligence = ContinuousIntelligence()
    domain = intelligence.discover_domain("Engineering")
    objective = intelligence.add_objective(
        StudyObjective("obj-1", domain.domain_id, "Build and validate a capability")
    )
    evidence = intelligence.record_evidence(
        Evidence("ev-1", objective.objective_id, "test-result", confidence=0.9)
    )
    experiment = intelligence.record_experiment(
        Experiment("exp-1", objective.objective_id, "sandbox", evidence_ids=(evidence.evidence_id,))
    )
    evaluation = intelligence.evaluate(
        Evaluation("eval-1", experiment.experiment_id, score=0.85, passed=True)
    )
    capability = intelligence.register_capability(
        Capability(
            capability_id="cap-1",
            domain_id=domain.domain_id,
            name="validated-engineering-capability",
            evaluation_ids=(evaluation.evaluation_id,),
        )
    )

    assert evidence.objective_id == objective.objective_id
    assert experiment.evidence_ids == (evidence.evidence_id,)
    assert evaluation.passed is True
    assert capability.evaluation_ids == (evaluation.evaluation_id,)


def test_knowledge_lifecycle_rejects_invalid_transition():
    intelligence = ContinuousIntelligence()
    knowledge = intelligence.create_knowledge("claim-1", KnowledgeState.CANDIDATE)

    with pytest.raises(ValueError):
        intelligence.transition_knowledge(knowledge.knowledge_id, KnowledgeState.VALIDATED)


def test_capability_cannot_be_registered_without_evaluation():
    intelligence = ContinuousIntelligence()
    domain = intelligence.discover_domain("Science")

    with pytest.raises(ValueError):
        intelligence.register_capability(
            Capability("cap-1", domain.domain_id, "unproven", evaluation_ids=())
        )

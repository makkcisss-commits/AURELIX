from aurelix_runtime.integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)


def test_complete_engine_chain_without_external_provider_stops_safely():
    store = EngineStore()
    research = ResearchEngine().run("test objective", store)
    academy = AcademyEngine().run(research, store)
    knowledge = KnowledgeEngine().run(academy, store)
    innovation = InnovationEngine().run(knowledge, store)
    experiment = ExperimentEngine().run(innovation, store)
    evaluation = EvaluationEngine().run(experiment, store)
    opportunity = OpportunityEngine().run(evaluation, store)
    business = BusinessEngine().run(opportunity, approved=False)

    assert research["objective"] == "test objective"
    assert research["status"] == "awaiting_provider"
    assert knowledge["knowledge_id"] is None
    assert experiment["experiment_id"] is None
    assert evaluation["passed"] is False
    assert opportunity["opportunity_id"] is None
    assert opportunity["status"] == "awaiting_validation"
    assert business["status"] == "awaiting_validation"
    assert store.knowledge == {}
    assert store.opportunities == {}


def test_validated_opportunity_is_the_only_path_to_business():
    store = EngineStore()
    evaluation = EvaluationEngine().run({"experiment_id": "exp-1"}, store)
    assert evaluation["passed"] is False
    blocked = OpportunityEngine().run(evaluation, store)
    assert blocked["opportunity_id"] is None

    opportunity = OpportunityEngine().run({"experiment_id": "exp-1", "passed": True}, store)
    assert opportunity["status"] == "validated"
    assert opportunity["opportunity_id"] in store.opportunities
    assert BusinessEngine(require_approval=True).run(opportunity, approved=False)["status"] == "awaiting_approval"
    assert BusinessEngine(require_approval=True).run(opportunity, approved=True)["status"] == "ready_for_execution"

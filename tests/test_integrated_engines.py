from aurelix_runtime.integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)


def test_complete_engine_chain_without_external_provider():
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
    assert knowledge["knowledge_id"] in store.knowledge
    assert experiment["experiment_id"] in store.experiments
    assert opportunity["opportunity_id"] in store.opportunities
    assert business["status"] == "awaiting_approval"
    assert len(store.audit) == 7

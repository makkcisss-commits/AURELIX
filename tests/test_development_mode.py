from aurelix_core.engine_factory import EngineFactory


def test_development_mode_builds_a_complete_offline_flow(monkeypatch):
    monkeypatch.setenv("AURELIX_MODE", "development")
    monkeypatch.delenv("AURELIX_MODEL_BASE_URL", raising=False)
    monkeypatch.delenv("AURELIX_RESEARCH_URL", raising=False)
    monkeypatch.delenv("AURELIX_RESEARCH_API_KEY", raising=False)
    monkeypatch.delenv("AURELIX_DATABASE_URL", raising=False)

    factory = EngineFactory()
    result = factory.research_and_store("development validation")

    assert result.evidence
    assert factory.knowledge.count() == 1

    flow = __import__("aurelix_core.intelligence_flow", fromlist=["IntelligenceFlow"]).IntelligenceFlow(factory)
    outcome = flow.research_to_experiment("development validation")
    experiment_id = outcome["experiment"]["experiment_id"]
    execution = flow.execute_experiment(experiment_id, [{"success": 1.0}])

    assert execution["status"] == "complete"
    assert execution["evaluation"]["passed"] is True

from decimal import Decimal
from types import SimpleNamespace

from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest


def test_unified_system_cycle_connects_intelligence_and_governance(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db"))))
    try:
        result = factory.run_system_cycle("find a bounded automation opportunity")
        assert result.enterprise["research"]["status"] == "completed"
        assert result.intelligence["status"] == "projected"
        assert result.governance["execution_allowed"] is False
        assert result.governance["route"] in {"POLICY_ALLOWED", "OWNER_REQUIRED", "BLOCKED"}
        assert result.economic_learning["context"]["execution_allowed"] is False
        assert result.diagnostics["status"] in {"ok", "degraded", "failed"}
    finally:
        factory.runtime.close()


def test_system_cycle_routes_through_canonical_economic_feedback(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db"))))
    try:
        feedback = {"average_realization_ratio": 1.25, "productive_sources": 2}; captured = {}
        monkeypatch.setattr(factory, "economic_learning_context", lambda: feedback)
        def run(objective, *, approved=False, economic_feedback=None):
            captured.update(objective=objective, approved=approved, economic_feedback=economic_feedback)
            return SimpleNamespace(objective=objective, research={"status": "completed"}, academy={"lessons": []}, knowledge={"knowledge_id": None}, innovation={}, experiment={}, evaluation={}, opportunity={}, business={}, status="awaiting_validation")
        monkeypatch.setattr(factory.enterprise, "run", run)
        monkeypatch.setattr(factory.system_orchestrator, "_project_academy", lambda *args: {"status": "awaiting_knowledge"})
        factory.run_system_cycle("use verified economics")
        assert captured == {"objective": "use verified economics", "approved": False, "economic_feedback": feedback}
    finally:
        factory.runtime.close()


def _authorized_decision(factory):
    return factory.governor.evaluate(DecisionRequest(actor=Actor(id="economic-observer", role="observer", autonomy=AutonomyLevel.A2), action=ActionClass.BUILD, reason="authorized economic observation"))


def test_verified_economic_outcome_becomes_idempotent_learning(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db"))))
    try:
        decision = _authorized_decision(factory)
        factory.record_verified_economic_outcome(opportunity_id="opp-1", source_id="source-1", expected_daily_eur=Decimal("10"), observed_daily_eur=Decimal("12"), governor_decision_id=decision.request_id, resource_scope="bounded", external_reference="external-1")
        first = factory.run_system_cycle("consume verified economics")
        second = factory.run_system_cycle("consume verified economics")
        assert first.economic_learning["new_signals"] == 1
        assert second.economic_learning["new_signals"] == 0
        assert first.economic_learning["signals"][0]["observed_daily_eur"] == "12"
        assert first.economic_learning["signals"][0]["realization_ratio"] == "1.2"
    finally:
        factory.runtime.close()


def test_verified_economic_signal_is_recorded_as_learning(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")
    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db"))))
    try:
        decision = _authorized_decision(factory)
        factory.record_verified_economic_outcome(opportunity_id="opp-learning", source_id="source-learning", expected_daily_eur=Decimal("20"), observed_daily_eur=Decimal("15"), governor_decision_id=decision.request_id, external_reference="external-learning-1")
        result = factory.run_system_cycle("consume economic result")
        items = result.economic_learning["learning_items"]
        assert len(items) == 1
        assert items[0]["outcome"] == "SUCCESS"
        assert "opp-learning" in items[0]["evidence_refs"]
        assert decision.request_id in items[0]["evidence_refs"]
        assert result.economic_learning["context"]["learning_item_count"] == 1
        assert result.economic_learning["context"]["execution_allowed"] is False
        assert factory.system_status()["learning_items"] == 1
    finally:
        factory.runtime.close()

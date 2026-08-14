from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_engine_factory_uses_runtime_store_for_knowledge(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        assert factory.knowledge.store is factory.runtime.store
        assert "autonomy.run" in factory.runtime.claimed_handlers
        assert factory.runtime.store.path == str(tmp_path / "aurelix.db")
    finally:
        factory.runtime.close()


def test_self_improvement_is_composed_and_closed_loop(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        assessment = factory.self_improvement_assess()
        assert assessment["report"]["checks"]
        prepared = factory.self_improvement_prepare("repair the weakest connected capability")
        assert prepared["status"] == "awaiting_approval"
        assert prepared["plan"]["id"]
    finally:
        factory.runtime.close()


def test_enterprise_cycle_automatically_passes_verified_economic_context(tmp_path, monkeypatch):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=False))
    try:
        feedback = {"verified_revenue_eur": 125.0, "verified_outcomes": 2}
        calls = {}

        monkeypatch.setattr(factory, "economic_learning_context", lambda: feedback)

        def run(objective, *, approved=False, economic_feedback=None):
            calls.update(objective=objective, approved=approved, economic_feedback=economic_feedback)
            return "cycle"

        monkeypatch.setattr(factory.enterprise, "run", run)

        assert factory.run_enterprise_cycle("find qualified B2B opportunities", approved=True) == "cycle"
        assert calls == {
            "objective": "find qualified B2B opportunities",
            "approved": True,
            "economic_feedback": feedback,
        }
    finally:
        factory.runtime.close()

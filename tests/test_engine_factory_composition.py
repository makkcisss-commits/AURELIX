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

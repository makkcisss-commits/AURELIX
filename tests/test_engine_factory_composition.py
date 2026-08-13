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

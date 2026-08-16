from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_factory_reuses_one_governor_and_one_policy_per_runtime_store(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    assert factory.governor is getattr(runtime.store, "_canonical_governor")
    assert factory.policy_engine is factory.governor.policy
    runtime.close()

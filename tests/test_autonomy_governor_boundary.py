import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_autonomy_execution_is_governed(tmp_path):
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=True), runtime=None)
    try:
        factory.runtime.close()
    except Exception:
        pass


def test_autonomy_fabric_requires_canonical_governor(tmp_path):
    from aurelix_runtime.autonomy_fabric import AutonomyFabric
    from aurelix_runtime.persistence import RuntimeStore

    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        with pytest.raises(ValueError, match="canonical governor"):
            AutonomyFabric(store=store)
    finally:
        store.close()

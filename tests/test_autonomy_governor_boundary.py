import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_core.governor import Governor
from aurelix_core.models import Decision, DecisionStatus
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class DenyingGovernor(Governor):
    def evaluate(self, request):
        return Decision(request.id, DecisionStatus.REJECTED, False, "test denial", False)


def test_autonomy_execution_is_blocked_by_governor(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=True), runtime=runtime)
    factory.autonomy_fabric.governor = DenyingGovernor(audit=factory.audit)
    with pytest.raises(PermissionError, match="denied by Governor"):
        factory.autonomy_fabric.run("must be blocked")
    record = runtime.store.get(next(iter([row["job_id"] for row in runtime.store.audit_summary(20)["recent"] if row["event_type"] == "autonomy.governor_denied"])))
    assert record is not None
    assert record.status == "failed"
    runtime.close()


def test_autonomy_fabric_requires_canonical_governor(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        from aurelix_runtime.autonomy_fabric import AutonomyFabric
        with pytest.raises(ValueError, match="canonical governor"):
            AutonomyFabric(store=store)
    finally:
        store.close()

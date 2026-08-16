import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_core.governor import Governor
from aurelix_core.policy import PolicyEngine
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class DenyingGovernor(Governor):
    def evaluate(self, request):
        decision = super().evaluate(request)
        from aurelix_core.models import Decision, DecisionStatus
        return Decision(request.id, DecisionStatus.REJECTED, False, "test denial", False)


def test_enterprise_cycle_records_governor_decision(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    cycle = factory.run_enterprise_cycle("governed objective")
    assert cycle.objective == "governed objective"
    events = runtime.store.audit_summary(50)["recent"]
    assert any(event["event_type"] == "decision.evaluated" for event in events)
    runtime.close()


def test_enterprise_loop_cannot_run_when_canonical_governor_denies(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    factory.enterprise.governor = DenyingGovernor(policy=PolicyEngine(), audit=factory.audit)
    with pytest.raises(PermissionError, match="denied by Governor"):
        factory.run_enterprise_cycle("must be blocked")
    runtime.close()

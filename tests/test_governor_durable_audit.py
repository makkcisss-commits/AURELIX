from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_engine_factory_uses_durable_audit_sink(tmp_path, monkeypatch):
    db_path = tmp_path / "runtime.db"
    monkeypatch.setenv("AURELIX_AUDIT_DB", str(db_path))
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(db_path)))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    request = DecisionRequest(
        actor=Actor(id="research-agent", role="research", autonomy=AutonomyLevel.A1),
        action=ActionClass.RESEARCH,
        reason="durable audit integration",
    )

    factory.governor.evaluate(request)

    events = runtime.store.audit_summary(20)["recent"]
    assert any(event["event_type"] == "decision.evaluated" and event["job_id"] == request.id for event in events)
    runtime.close()

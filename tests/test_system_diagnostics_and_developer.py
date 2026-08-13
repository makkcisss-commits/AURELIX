from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_diagnostics_and_developer_are_composed(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        report = factory.diagnose()
        assert report["status"] in {"ok", "degraded", "failed"}
        names = {check["name"] for check in report["checks"]}
        assert {"runtime", "knowledge_store", "enterprise_loop", "developer_control"} <= names

        plan = factory.plan_system_change("improve the connected enterprise loop")
        assert plan["status"] == "awaiting_approval"
        assert plan["id"]
        approved = factory.system_developer.approve(plan, True)
        assert approved["status"] == "approved"
    finally:
        factory.runtime.close()

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_system_closure_contract_is_one_machine(tmp_path):
    factory = EngineFactory(
        EngineFactoryConfig(
            runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")),
            register_autonomy=True,
        )
    )
    try:
        assert factory.autonomy_fabric is not None
        assert factory.autonomy_fabric.engines is factory.enterprise.store
        assert factory.autonomy_fabric.message_fabric is factory.message_fabric
        assert factory.autonomy_fabric.research is factory.research
        assert factory.autonomy_fabric.academy is factory.academy
        assert factory.autonomy_fabric.opportunity is factory.opportunity
        assert factory.autonomy_fabric.business is factory.business

        validation = factory.validate_system()
        assert validation["status"] == "ok"
        assert validation["summary"]["failed"] == 0

        economic = factory.economic_learning_context()
        assert economic["verified_financial_outcome"] is False
        assert economic["daily_realized_eur"] == 0

        diagnostic = factory.diagnose()
        assert diagnostic["status"] in {"ok", "degraded"}
    finally:
        factory.runtime.close()

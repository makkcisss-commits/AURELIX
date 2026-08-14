from decimal import Decimal


def test_unified_system_cycle_connects_intelligence_and_governance(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")

    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig

    factory = EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    )
    try:
        result = factory.run_system_cycle("find a bounded automation opportunity")

        assert result.enterprise["research"]["status"] == "completed"
        assert result.intelligence["status"] == "projected"
        assert result.governance["execution_allowed"] is False
        assert result.governance["route"] in {"POLICY_ALLOWED", "OWNER_REQUIRED", "BLOCKED"}
        assert result.economic_learning["context"]["execution_allowed"] is False
        assert result.diagnostics["status"] in {"ok", "degraded", "failed"}
    finally:
        factory.runtime.close()


def test_verified_economic_outcome_becomes_idempotent_learning(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")

    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig

    factory = EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    )
    try:
        factory.record_verified_economic_outcome(
            opportunity_id="opp-1",
            source_id="source-1",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("12"),
            governor_decision_id="decision-1",
            resource_scope="bounded",
            external_reference="external-1",
        )
        first = factory.run_system_cycle("consume verified economics")
        second = factory.run_system_cycle("consume verified economics")

        assert first.economic_learning["new_signals"] == 1
        assert second.economic_learning["new_signals"] == 0
        assert first.economic_learning["signals"][0]["observed_daily_eur"] == "12"
        assert first.economic_learning["signals"][0]["realization_ratio"] == "1.2"
    finally:
        factory.runtime.close()

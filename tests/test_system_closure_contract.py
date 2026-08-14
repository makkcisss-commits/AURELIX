from __future__ import annotations


def test_development_mode_never_claims_real_opportunity_evidence(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")

    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig

    factory = EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    )
    try:
        diagnostic = factory.diagnose()
        check = next(item for item in diagnostic["checks"] if item["name"] == "live_opportunity_readiness")
        assert check["status"] == "degraded"
        assert check["evidence"]["real_evidence"] is False
    finally:
        factory.runtime.close()


def test_canonical_composition_has_shared_engine_store(monkeypatch, tmp_path):
    monkeypatch.setenv("AURELIX_MODE", "development")

    from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
    from aurelix_runtime.runtime import RuntimeConfig

    factory = EngineFactory(
        EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    )
    try:
        diagnostic = factory.diagnose()
        check = next(item for item in diagnostic["checks"] if item["name"] == "canonical_composition")
        assert check["status"] == "ok"
        assert all(check["evidence"].values())
    finally:
        factory.runtime.close()

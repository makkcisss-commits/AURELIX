from decimal import Decimal

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


def test_autonomy_and_enterprise_share_the_same_composition(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        fabric = factory.autonomy_fabric
        assert fabric is not None
        assert fabric.engines is factory.enterprise.store
        assert fabric.message_fabric is factory.message_fabric
        assert fabric.research is factory.research
        assert fabric.academy is factory.academy
        assert fabric.knowledge is factory.knowledge_engine
        assert fabric.innovation is factory.innovation
        assert fabric.experiment is factory.experiment
        assert fabric.evaluation is factory.evaluation
        assert fabric.opportunity is factory.opportunity
        assert fabric.business is factory.business
    finally:
        factory.runtime.close()


def test_system_validation_catches_and_accepts_canonical_composition(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        report = factory.validate_system()
        checks = {item["name"]: item for item in report["checks"]}
        assert checks["canonical_composition"]["status"] == "ok"
        assert checks["economic_feedback"]["status"] == "ok"
    finally:
        factory.runtime.close()


def test_economic_feedback_does_not_claim_verified_revenue_without_observation(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=False))
    try:
        context = factory.economic_learning_context()
        assert context["daily_realized_eur"] == Decimal("0")
        assert context["verified_financial_outcome"] is False
        assert context["productive_sources"] == 0
    finally:
        factory.runtime.close()


def test_self_improvement_is_composed_and_closed_loop(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=True))
    try:
        assessment = factory.self_improvement_assess()
        assert assessment["report"]["checks"]
        prepared = factory.self_improvement_prepare("repair the weakest connected capability")
        assert prepared["status"] == "awaiting_approval"
        assert prepared["plan"]["id"]
    finally:
        factory.runtime.close()


def test_enterprise_cycle_automatically_passes_verified_economic_context(tmp_path, monkeypatch):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=False))
    try:
        feedback = {"verified_revenue_eur": 125.0, "verified_outcomes": 2}
        calls = {}

        monkeypatch.setattr(factory, "economic_learning_context", lambda: feedback)

        def run(objective, *, approved=False, economic_feedback=None):
            calls.update(objective=objective, approved=approved, economic_feedback=economic_feedback)
            return "cycle"

        monkeypatch.setattr(factory.enterprise, "run", run)

        assert factory.run_enterprise_cycle("find qualified B2B opportunities", approved=True) == "cycle"
        assert calls == {
            "objective": "find qualified B2B opportunities",
            "approved": True,
            "economic_feedback": feedback,
        }
    finally:
        factory.runtime.close()


def test_system_orchestrator_uses_factory_owned_academy_and_intelligence(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=False))
    try:
        assert factory.system_orchestrator.intelligence is factory.continuous_intelligence
        assert factory.system_orchestrator.curated_academy is factory.curated_academy
        assert factory.system_orchestrator.academy_bridge.intelligence is factory.continuous_intelligence
    finally:
        factory.runtime.close()


def test_factory_exposes_canonical_opportunity_revenue_bridge(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), register_autonomy=False))
    try:
        assert factory.opportunity_revenue_bridge.revenue is factory.revenue
    finally:
        factory.runtime.close()

from decimal import Decimal

import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from aurelix_core.system_orchestrator import SystemOrchestrator
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_verified_economic_outcome_requires_real_governor_decision(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    with pytest.raises(PermissionError, match="does not exist"):
        factory.record_verified_economic_outcome(
            opportunity_id="opp-1",
            source_id="source-1",
            expected_daily_eur=Decimal("10"),
            observed_daily_eur=Decimal("12"),
            governor_decision_id="forged-decision",
            external_reference="external-1",
        )
    runtime.close()


def test_verified_economic_outcome_survives_runtime_restart(tmp_path):
    db_path = tmp_path / "runtime.db"
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(db_path)))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    decision = factory.governor.evaluate(DecisionRequest(
        actor=Actor(id="economic-observer", role="observer", autonomy=AutonomyLevel.A2),
        action=ActionClass.BUILD,
        reason="authorized economic observation",
    ))
    entry = factory.record_verified_economic_outcome(
        opportunity_id="opp-1",
        source_id="source-1",
        expected_daily_eur=Decimal("10"),
        observed_daily_eur=Decimal("12"),
        governor_decision_id=decision.request_id,
        external_reference="external-1",
    )
    assert entry.observed_daily_eur == Decimal("12")
    runtime.close()

    runtime2 = AurelixRuntime(RuntimeConfig(database_path=str(db_path)))
    factory2 = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime2)
    restored = factory2.system_orchestrator.economic_ledger.all()
    assert len(restored) == 1
    assert restored[0].external_reference == "external-1"
    assert restored[0].observed_daily_eur == Decimal("12")
    runtime2.close()


def test_external_reference_is_idempotent_and_conflict_safe(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    factory = EngineFactory(config=EngineFactoryConfig(register_autonomy=False), runtime=runtime)
    decision = factory.governor.evaluate(DecisionRequest(
        actor=Actor(id="economic-observer", role="observer", autonomy=AutonomyLevel.A2),
        action=ActionClass.BUILD,
        reason="authorized economic observation",
    ))
    kwargs = dict(
        opportunity_id="opp-1",
        source_id="source-1",
        expected_daily_eur=Decimal("10"),
        observed_daily_eur=Decimal("12"),
        governor_decision_id=decision.request_id,
        external_reference="external-1",
    )
    first = factory.record_verified_economic_outcome(**kwargs)
    second = factory.record_verified_economic_outcome(**kwargs)
    assert first == second
    with pytest.raises(ValueError, match="different economic observation"):
        factory.record_verified_economic_outcome(**{**kwargs, "observed_daily_eur": Decimal("99")})
    runtime.close()

from aurelix_core.engine_factory import EngineFactory
from aurelix_core.continuous_intelligence import EvidenceKind
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_canonical_composition_shares_one_adaptive_loop() -> None:
    factory = EngineFactory()
    assert factory.autonomy_fabric is not None
    assert factory.adaptive_loop.intelligence is factory.continuous_intelligence
    assert factory.adaptive_loop.capability_escalator is factory.capability_escalator
    assert factory.autonomy_fabric.adaptive_loop is factory.adaptive_loop

    execution_id = "adaptive-test"
    factory.adaptive_loop.register_mission(
        execution_id, "validate a new business capability", ["crm-write"]
    )
    mission, objective = factory.adaptive_loop.block_for_capability(
        execution_id,
        "crm-write",
        reason="the runtime has no validated CRM write capability",
        requested_by="test",
    )

    assert mission.blocked is True
    assert objective.objective_id in factory.continuous_intelligence.objectives
    assert factory.adaptive_loop.can_resume(execution_id) is False

    evidence = factory.adaptive_loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="test://crm-write/proof",
        strength=1.0,
    )
    evaluation = factory.continuous_intelligence.evaluate(
        objective_id=objective.objective_id,
        score=1.0,
        evidence_refs=(evidence.evidence_id,),
    )
    factory.adaptive_loop.validate_learning(
        execution_id=execution_id,
        capability="crm-write",
        objective_id=objective.objective_id,
        evaluation_id=evaluation.evaluation_id,
        evidence_refs=(evidence.evidence_id,),
    )

    assert factory.adaptive_loop.can_resume(execution_id) is True
    resumed = factory.adaptive_loop.resume_ready(execution_id)
    assert resumed.blocked is False
    factory.autonomy_fabric.close()


def test_validated_capability_survives_runtime_restart(tmp_path):
    db = tmp_path / "adaptive-capability.db"
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(db)))
    factory = EngineFactory(runtime=runtime)
    factory.adaptive_loop._persist_validated_capability("crm-write")
    assert factory.adaptive_loop.capability_validated("crm-write") is True
    runtime.store.close()

    restarted = AurelixRuntime(RuntimeConfig(database_path=str(db)))
    restarted_factory = EngineFactory(runtime=restarted)
    restarted_factory.adaptive_loop.register_mission(
        "resume-after-restart", "resume a validated capability", ["crm-write"]
    )
    assert restarted_factory.adaptive_loop.can_resume("resume-after-restart") is True
    restarted.store.close()

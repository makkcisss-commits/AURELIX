from aurelix_core.engine_factory import EngineFactory
from aurelix_core.continuous_intelligence import EvidenceKind


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
    factory.continuous_intelligence.validate_capability(
        name="crm-write",
        domain="capability-development",
        required_competencies=("crm-write",),
        evidence_refs=(evidence.evidence_id,),
    )

    assert factory.adaptive_loop.can_resume(execution_id) is True

    parent = factory.runtime.store.enqueue(
        "autonomy.run",
        {"objective": mission.objective, "mission_id": mission.mission_id},
        execution_id=execution_id,
    )
    claimed = factory.runtime.store.claim(parent.job_id, worker_id="test-worker")
    assert claimed is not None
    factory.runtime.store.complete(
        execution_id,
        {
            "execution_id": execution_id,
            "mission_id": mission.mission_id,
            "status": "capability_learning_required",
        },
        worker_id=claimed.worker_id,
        lease_token=claimed.lease_token,
    )

    resumed = factory.adaptive_loop.resume_ready(execution_id)
    assert resumed.blocked is False
    child = factory.runtime.store.status()["queued"]
    assert child >= 1
    factory.autonomy_fabric.close()

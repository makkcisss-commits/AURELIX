from aurelix_core.engine_factory import EngineFactory
from aurelix_core.continuous_intelligence import EvidenceKind
from aurelix_runtime.job_queue import PersistentJobQueue


def test_canonical_composition_shares_one_adaptive_loop() -> None:
    factory = EngineFactory()
    assert factory.autonomy_fabric is not None
    assert factory.adaptive_loop.intelligence is factory.continuous_intelligence
    assert factory.adaptive_loop.capability_escalator is factory.capability_escalator
    assert factory.autonomy_fabric.adaptive_loop is factory.adaptive_loop

    execution_id = "adaptive-test"
    mission_id = "mission-adaptive-test"
    factory.adaptive_loop.register_mission(
        execution_id, "validate a new business capability", ["crm-write"], mission_id=mission_id
    )
    queue = PersistentJobQueue(store=factory.runtime.store, engine_store=factory.enterprise.store)
    queue.enqueue(execution_id, "validate a new business capability")
    mission, objective = factory.adaptive_loop.block_for_capability(
        execution_id,
        "crm-write",
        reason="the runtime has no validated CRM write capability",
        requested_by="test",
    )

    assert mission.blocked is True
    assert mission.mission_id == mission_id
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
    resumed = factory.adaptive_loop.resume_ready(execution_id)
    assert resumed.blocked is False
    assert resumed.mission_id == mission_id
    resumed_execution = next(
        row["execution_id"]
        for row in [factory.runtime.store.db.execute(
            "SELECT value FROM runtime_state WHERE key=?", (f"mission-resume:{mission_id}",)
        ).fetchone()]
        if row is not None
        for row in [{"execution_id": __import__("json").loads(row[0])["execution_id"]}]
    )
    assert resumed_execution != execution_id
    assert factory.runtime.store.get(execution_id).status == "queued"
    assert factory.runtime.store.get(resumed_execution).status == "queued"
    factory.autonomy_fabric.close()
    factory.runtime.close()

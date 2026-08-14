from aurelix_core.continuous_intelligence import EvidenceKind
from aurelix_core.engine_factory import EngineFactory


def test_capability_block_is_resumable_with_same_mission_id() -> None:
    factory = EngineFactory()
    execution_id = "resume-test"
    result = factory.autonomy_fabric.run(
        "resume a blocked mission",
        execution_id=execution_id,
        required_capabilities=["crm-write"],
    )
    assert result.status == "capability_learning_required"
    assert result.mission_id
    assert factory.autonomy_fabric.store.get_result(execution_id)["mission_id"] == result.mission_id
    assert factory.adaptive_loop.can_resume(execution_id) is False

    objective = next(iter(factory.continuous_intelligence.objectives.values()))
    evidence = factory.adaptive_loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="test://crm-write/resume-proof",
        strength=1.0,
    )
    factory.continuous_intelligence.validate_capability(
        name="crm-write",
        domain=objective.domain,
        required_competencies=objective.target_competencies,
        evidence_refs=(evidence.evidence_id,),
    )

    resumed = factory.autonomy_fabric.resume_mission(execution_id)
    assert resumed.mission_id == result.mission_id
    assert resumed.status != "capability_learning_required"
    factory.autonomy_fabric.close()


def test_unvalidated_capability_cannot_resume() -> None:
    factory = EngineFactory()
    execution_id = "resume-negative-test"
    result = factory.autonomy_fabric.run(
        "do not resume an unvalidated mission",
        execution_id=execution_id,
        required_capabilities=["crm-write"],
    )
    assert result.status == "capability_learning_required"
    try:
        factory.autonomy_fabric.resume_mission(execution_id)
    except RuntimeError as exc:
        assert "not validated" in str(exc)
    else:
        raise AssertionError("unvalidated capability unexpectedly resumed")
    factory.autonomy_fabric.close()

import pytest

from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence, EvidenceKind


def build_loop() -> AdaptiveLoop:
    intelligence = ContinuousIntelligence()
    return AdaptiveLoop(intelligence, CapabilityEscalator(intelligence))


def test_shared_loop_learning_pass_validates_capability_and_resumes_same_mission() -> None:
    loop = build_loop()
    mission = loop.register_mission("mission-1", "execute CRM workflow", ["crm-write"])
    blocked, objective = loop.block_for_capability(
        mission.execution_id,
        "crm-write",
        reason="CRM write operation is not available",
        requested_by="business",
    )

    assert blocked.blocked is True
    assert blocked.execution_id == mission.execution_id

    experiment = loop.intelligence.propose_experiment(
        objective_id=objective.objective_id,
        hypothesis="CRM write succeeds under the governed test contract",
        method="execute isolated CRM write benchmark",
        success_criteria=("write succeeds", "no authorization bypass"),
    )
    evidence = loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference=experiment.experiment_id,
        strength=0.95,
    )
    evaluation = loop.intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.9,
        evidence_refs=(evidence.evidence_id,),
    )

    assert loop.can_resume(mission.execution_id) is False

    capability = loop.validate_learning(
        execution_id=mission.execution_id,
        capability="crm-write",
        objective_id=objective.objective_id,
        evaluation_id=evaluation.evaluation_id,
        evidence_refs=(evidence.evidence_id,),
    )

    assert capability.validated is True
    resumed = loop.resume_ready(mission.execution_id)
    assert resumed.execution_id == mission.execution_id
    assert resumed.blocked is False
    assert resumed.objective == mission.objective


def test_failed_learning_never_unlocks_business_mission() -> None:
    loop = build_loop()
    mission = loop.register_mission("mission-2", "execute CRM workflow", ["crm-write"])
    _, objective = loop.block_for_capability(
        mission.execution_id,
        "crm-write",
        reason="CRM write operation is not available",
        requested_by="business",
    )
    evidence = loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="failed-crm-test",
        strength=0.4,
    )
    evaluation = loop.intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.4,
        evidence_refs=(evidence.evidence_id,),
    )

    assert evaluation.status.value == "FAILED"
    with pytest.raises(RuntimeError, match="did not pass"):
        loop.validate_learning(
            execution_id=mission.execution_id,
            capability="crm-write",
            objective_id=objective.objective_id,
            evaluation_id=evaluation.evaluation_id,
            evidence_refs=(evidence.evidence_id,),
        )

    assert loop.can_resume(mission.execution_id) is False
    with pytest.raises(RuntimeError, match="not validated"):
        loop.resume_ready(mission.execution_id)

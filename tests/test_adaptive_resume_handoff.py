from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence, EvidenceKind


def test_validated_learning_hands_mission_to_runtime_executor():
    intelligence = ContinuousIntelligence()
    escalator = CapabilityEscalator(intelligence)
    loop = AdaptiveLoop(intelligence, escalator)
    loop.register_mission("exec-1", "deliver research", ["special-capability"])
    _, objective = loop.block_for_capability(
        "exec-1", "special-capability", reason="missing", requested_by="runtime"
    )
    evidence = loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="experiment://exec-1",
        strength=0.95,
    )
    evaluation = intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.95,
        evidence_refs=(evidence.evidence_id,),
    )
    loop.validate_learning(
        execution_id="exec-1",
        capability="special-capability",
        objective_id=objective.objective_id,
        evaluation_id=evaluation.evaluation_id,
        evidence_refs=(evidence.evidence_id,),
    )

    handoffs = []
    loop.set_resume_executor(handoffs.append)
    mission = loop.resume_ready("exec-1")

    assert mission.blocked is False
    assert handoffs == [mission]


def test_failed_learning_never_hands_mission_to_runtime():
    intelligence = ContinuousIntelligence()
    escalator = CapabilityEscalator(intelligence)
    loop = AdaptiveLoop(intelligence, escalator)
    loop.register_mission("exec-2", "deliver research", ["special-capability"])
    _, objective = loop.block_for_capability(
        "exec-2", "special-capability", reason="missing", requested_by="runtime"
    )
    evidence = loop.record_evidence(
        objective_id=objective.objective_id,
        kind=EvidenceKind.EXPERIMENT,
        reference="experiment://exec-2",
        strength=0.2,
    )
    evaluation = intelligence.evaluate(
        objective_id=objective.objective_id,
        score=0.2,
        evidence_refs=(evidence.evidence_id,),
    )
    try:
        loop.validate_learning(
            execution_id="exec-2",
            capability="special-capability",
            objective_id=objective.objective_id,
            evaluation_id=evaluation.evaluation_id,
            evidence_refs=(evidence.evidence_id,),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("failed learning must never validate a capability")

    handoffs = []
    loop.set_resume_executor(handoffs.append)
    try:
        loop.resume_ready("exec-2")
    except RuntimeError:
        pass
    else:
        raise AssertionError("unvalidated capability must keep mission blocked")
    assert handoffs == []

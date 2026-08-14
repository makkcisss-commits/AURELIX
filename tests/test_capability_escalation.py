from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence


def test_unknown_capability_becomes_academy_objective_and_is_deduplicated():
    intelligence = ContinuousIntelligence()
    escalator = CapabilityEscalator(intelligence)

    first_gap, first_objective = escalator.escalate(
        capability="negotiate enterprise partnership",
        reason="no validated negotiation capability is available",
        requested_by="business",
    )
    second_gap, second_objective = escalator.escalate(
        capability="negotiate enterprise partnership",
        reason="no validated negotiation capability is available",
        requested_by="orchestrator",
    )

    assert first_gap.gap_id == second_gap.gap_id
    assert first_objective.objective_id == second_objective.objective_id
    assert len(intelligence.objectives) == 1
    assert first_objective.domain == "capability-development"
    assert first_objective.target_competencies == ("negotiate enterprise partnership",)


def test_invalid_escalation_is_rejected():
    escalator = CapabilityEscalator(ContinuousIntelligence())
    try:
        escalator.escalate(capability="", reason="missing", requested_by="agent")
    except ValueError as exc:
        assert "required" in str(exc)
    else:
        raise AssertionError("empty capability must be rejected")

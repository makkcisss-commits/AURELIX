from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence


def test_adaptive_mission_preserves_canonical_mission_id_across_state_changes() -> None:
    intelligence = ContinuousIntelligence()
    loop = AdaptiveLoop(intelligence, CapabilityEscalator(intelligence))
    mission = loop.register_mission("execution-1", "execute governed workflow", ["crm-write"], mission_id="mission-1")
    assert mission.mission_id == "mission-1"
    blocked, _ = loop.block_for_capability(mission.execution_id, "crm-write", reason="capability missing", requested_by="test")
    assert blocked.mission_id == "mission-1"
    assert blocked.execution_id == "execution-1"


def test_resume_state_keeps_mission_identity_distinct_from_execution_identity() -> None:
    intelligence = ContinuousIntelligence()
    loop = AdaptiveLoop(intelligence, CapabilityEscalator(intelligence))
    mission = loop.register_mission("execution-1", "resume governed workflow", ["crm-write"], mission_id="mission-1")
    resumed = loop.register_mission("execution-2", mission.objective, mission.required_capabilities, mission_id=mission.mission_id)
    assert resumed.mission_id == mission.mission_id
    assert resumed.execution_id != mission.execution_id


def test_resume_handoff_failure_does_not_unblock_mission() -> None:
    intelligence = ContinuousIntelligence()
    loop = AdaptiveLoop(intelligence, CapabilityEscalator(intelligence))
    mission = loop.register_mission("execution-1", "resume governed workflow", ["crm-write"], mission_id="mission-1")
    loop.block_for_capability(mission.execution_id, "crm-write", reason="capability missing", requested_by="test")
    loop.set_resume_executor(lambda _mission: (_ for _ in ()).throw(RuntimeError("runtime unavailable")))
    try:
        loop.resume_ready(mission.execution_id)
    except RuntimeError:
        pass
    else:
        raise AssertionError("runtime handoff failure must block the resume transition")
    assert loop.missions[mission.execution_id].blocked is True

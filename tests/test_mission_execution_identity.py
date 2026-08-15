from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from aurelix_core.continuous_intelligence import ContinuousIntelligence


def test_adaptive_mission_preserves_canonical_mission_id_across_state_changes() -> None:
    intelligence = ContinuousIntelligence()
    loop = AdaptiveLoop(intelligence, CapabilityEscalator(intelligence))

    mission = loop.register_mission(
        "execution-1",
        "execute governed workflow",
        ["crm-write"],
        mission_id="mission-1",
    )
    assert mission.mission_id == "mission-1"
    blocked, _ = loop.block_for_capability(
        mission.execution_id,
        "crm-write",
        reason="capability missing",
        requested_by="test",
    )
    assert blocked.mission_id == "mission-1"
    assert blocked.execution_id == "execution-1"

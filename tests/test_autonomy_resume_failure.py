import pytest

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.mission_resume import MissionResumeCoordinator
from aurelix_runtime.persistence import RuntimeStore


class _ValidatedAdaptiveLoop:
    def register_mission(self, *_args, **_kwargs):
        return None

    def can_resume(self, _execution_id):
        return True


def test_resume_mission_propagates_execution_failure(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    coordinator = MissionResumeCoordinator(store)
    coordinator.register(
        mission_id="mission-failure",
        objective="resume safely",
        required_capabilities=["research-x"],
    )
    coordinator.block(
        mission_id="mission-failure",
        execution_id="parent-execution",
        reason="capability_learning_required",
    )

    fabric = AutonomyFabric.__new__(AutonomyFabric)
    fabric.store = store
    fabric.resume_coordinator = coordinator
    fabric.adaptive_loop = _ValidatedAdaptiveLoop()
    fabric.run_claimed = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("resume execution failed"))

    with pytest.raises(RuntimeError, match="resume execution failed"):
        fabric.resume_mission("mission-failure")

    state = coordinator.get("mission-failure")
    assert state is not None
    assert state.status == "blocked"
    assert state.active_execution_id is None
    assert state.parent_execution_id == "parent-execution"
    assert state.failed_execution_id is not None

    failed = store.get(state.failed_execution_id)
    assert failed is not None
    assert failed.status == "failed"
    store.close()

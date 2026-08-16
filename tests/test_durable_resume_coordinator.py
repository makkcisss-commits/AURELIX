import pytest

from aurelix_core.adaptive_loop import AdaptiveMission
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.resume_coordinator import DurableResumeCoordinator


def _completed_parent(store: RuntimeStore, parent_id: str, mission_id: str, status: str = "capability_learning_required") -> None:
    queued = store.enqueue("autonomy.run", {"objective": "continue", "required_capabilities": ["new-capability"]}, execution_id=parent_id)
    claimed = store.claim(queued.job_id, worker_id="worker-a")
    assert claimed is not None
    store.complete(parent_id, {"status": status, "mission_id": mission_id}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)


def test_resume_creates_distinct_execution_and_preserves_parent(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        parent_id = "execution-parent"
        mission_id = "mission-1"
        _completed_parent(store, parent_id, mission_id)
        mission = AdaptiveMission(parent_id, "continue", ("new-capability",), mission_id=mission_id)
        coordinator = DurableResumeCoordinator(store)
        child_id = coordinator.resume(mission)
        replay = coordinator.resume(mission)
        assert child_id != parent_id
        assert replay == child_id
        parent = store.get(parent_id)
        child = store.get(child_id)
        assert parent is not None and parent.status == "completed"
        assert child is not None and child.status == "queued"
        assert child.payload["mission_id"] == mission_id
        assert child.payload["parent_execution_id"] == parent_id
        assert store.get_result(parent_id) == {"status": "capability_learning_required", "mission_id": mission_id}
        assert store.get_result(child_id) is None
    finally:
        store.close()


def test_resume_rejects_running_parent_and_identity_mismatch(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        queued = store.enqueue("autonomy.run", {"objective": "continue"}, execution_id="running-parent")
        assert store.claim(queued.job_id, worker_id="worker-a") is not None
        coordinator = DurableResumeCoordinator(store)
        with pytest.raises(RuntimeError, match="cannot resume"):
            coordinator.resume(AdaptiveMission("running-parent", "continue", (), mission_id="mission-1"))

        _completed_parent(store, "completed-parent", "mission-1")
        with pytest.raises(RuntimeError, match="does not match"):
            coordinator.resume(AdaptiveMission("completed-parent", "continue", (), mission_id="wrong-mission"))
    finally:
        store.close()


def test_resume_rejects_non_blocked_completed_execution(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        _completed_parent(store, "completed", "mission-1", status="completed")
        with pytest.raises(RuntimeError, match="blocked mission"):
            DurableResumeCoordinator(store).resume(AdaptiveMission("completed", "continue", (), mission_id="mission-1"))
    finally:
        store.close()

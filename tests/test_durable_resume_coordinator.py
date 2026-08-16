from aurelix_core.adaptive_loop import AdaptiveMission
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.resume_coordinator import DurableResumeCoordinator


def test_resume_creates_distinct_execution_and_preserves_parent(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        parent_id = "execution-parent"
        mission_id = "mission-1"
        queued = store.enqueue(
            "autonomy.run",
            {"objective": "continue", "required_capabilities": ["new-capability"]},
            execution_id=parent_id,
        )
        claimed = store.claim(queued.job_id, worker_id="worker-a")
        assert claimed is not None
        parent_result = {"status": "capability_learning_required", "mission_id": mission_id}
        store.complete(parent_id, parent_result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)

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
        assert store.get_result(parent_id) == parent_result
        assert store.get_result(child_id) is None
    finally:
        store.close()

from aurelix_core.adaptive_loop import AdaptiveMission
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.resume_coordinator import DurableResumeCoordinator


def test_resume_creates_distinct_execution_attempt_and_preserves_parent(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        execution_id = "exec-resume-1"
        mission_id = "mission-1"
        queued = store.enqueue(
            "autonomy.run",
            {"objective": "continue mission", "required_capabilities": []},
            execution_id=execution_id,
        )
        claimed = store.claim(queued.job_id, worker_id="worker-1")
        assert claimed is not None
        original_result = {"status": "capability_learning_required"}
        store.complete(
            execution_id,
            original_result,
            worker_id=claimed.worker_id,
            lease_token=claimed.lease_token,
        )

        mission = AdaptiveMission(
            execution_id=execution_id,
            mission_id=mission_id,
            objective="continue mission",
            required_capabilities=("new-capability",),
            blocked=False,
        )
        coordinator = DurableResumeCoordinator(store)
        resumed = coordinator.resume(mission)
        resumed_again = coordinator.resume(mission)

        assert resumed != execution_id
        assert resumed_again == resumed
        parent = store.get(execution_id)
        child = store.get(resumed)
        assert parent is not None and parent.status == "completed"
        assert child is not None and child.status == "queued"
        assert child.payload["mission_id"] == mission_id
        assert child.payload["parent_execution_id"] == execution_id
        assert store.get_result(execution_id) == original_result
        assert store.get_result(resumed) is None

        with store.lock:
            count = store.db.execute(
                "SELECT COUNT(*) FROM jobs WHERE job_id LIKE ?", (f"{mission_id}:resume:%",)
            ).fetchone()[0]
        assert count == 1
    finally:
        store.close()


def test_resume_refuses_non_terminal_or_unknown_execution(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        coordinator = DurableResumeCoordinator(store)
        mission = AdaptiveMission("missing", "continue", ("cap",), blocked=False)
        try:
            coordinator.resume(mission)
        except KeyError:
            pass
        else:
            raise AssertionError("unknown execution must not be resumed")

        queued = store.enqueue(
            "autonomy.run", {"objective": "continue"}, execution_id="exec-running"
        )
        claimed = store.claim(queued.job_id, worker_id="worker-2")
        assert claimed is not None
        running = AdaptiveMission("exec-running", "continue", (), blocked=False)
        try:
            coordinator.resume(running)
        except RuntimeError:
            pass
        else:
            raise AssertionError("running execution must not be reopened")
    finally:
        store.close()

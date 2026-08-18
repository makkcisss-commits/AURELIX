from aurelix_core.adaptive_loop import AdaptiveMission
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.resume_coordinator import DurableResumeCoordinator


def test_resume_requeues_same_execution_id_without_creating_duplicate_job(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    try:
        execution_id = "exec-resume-1"
        queued = store.enqueue(
            "autonomy.run",
            {"objective": "continue mission", "required_capabilities": []},
            execution_id=execution_id,
        )
        claimed = store.claim(queued.job_id, worker_id="worker-1")
        assert claimed is not None
        store.complete(
            execution_id,
            {"status": "capability_learning_required"},
            worker_id=claimed.worker_id,
            lease_token=claimed.lease_token,
        )

        mission = AdaptiveMission(
            execution_id=execution_id,
            objective="continue mission",
            required_capabilities=("new-capability",),
            blocked=False,
        )
        resumed = DurableResumeCoordinator(store).resume(mission)

        assert resumed == execution_id
        record = store.get(execution_id)
        assert record is not None
        assert record.status == "queued"
        assert record.attempts == 0
        assert store.get_result(execution_id) is None

        # The primary key remains the original execution id: no second job exists.
        with store.lock:
            count = store.db.execute("SELECT COUNT(*) FROM jobs WHERE job_id=?", (execution_id,)).fetchone()[0]
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

        queued = store.enqueue("autonomy.run", {"objective": "continue"}, execution_id="exec-running")
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

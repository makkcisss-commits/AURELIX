from aurelix_runtime.job_queue import PersistentJobQueue
from aurelix_runtime.persistence import RuntimeStore


def make_queue(tmp_path):
    return PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))


def test_queue_claim_execute_and_recovery(tmp_path):
    queue = make_queue(tmp_path)
    queue.enqueue("job-1", "objective")
    result = queue.execute("job-1")
    assert result.status == "awaiting_approval"
    assert queue.jobs["job-1"].status == "completed"
    assert queue.store.get_result("job-1")["status"] == "awaiting_approval"
    queue.close()


def test_running_jobs_are_recoverable(tmp_path):
    queue = make_queue(tmp_path)
    queue.enqueue("job-2", "objective")
    queue.claim("job-2")
    assert queue.jobs["job-2"].status == "running"
    assert queue.recover_running() == 1
    assert queue.jobs["job-2"].status == "queued"
    queue.close()


def test_execution_id_is_unique(tmp_path):
    queue = make_queue(tmp_path)
    queue.enqueue("same-id", "first")
    try:
        queue.enqueue("same-id", "second")
    except Exception as exc:
        assert "UNIQUE" in str(exc).upper() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("duplicate execution_id must be rejected")
    queue.close()

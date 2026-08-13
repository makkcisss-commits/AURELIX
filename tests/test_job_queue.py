from concurrent.futures import ThreadPoolExecutor
from aurelix_runtime.job_queue import PersistentJobQueue
from aurelix_runtime.persistence import RuntimeStore

def make_queue(tmp_path): return PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))

def test_queue_claim_execute_and_recovery(tmp_path):
    queue = make_queue(tmp_path); queue.enqueue("job-1", "objective")
    result = queue.execute("job-1")
    assert result.status == "awaiting_approval"; assert queue.jobs["job-1"].status == "completed"; assert queue.store.get_result("job-1")["status"] == "awaiting_approval"; queue.close()

def test_running_jobs_are_recoverable(tmp_path):
    queue = make_queue(tmp_path); queue.enqueue("job-2", "objective"); queue.claim("job-2")
    assert queue.jobs["job-2"].status == "running"; assert queue.recover_running(stale_after_seconds=0) == 1; assert queue.jobs["job-2"].status == "queued"; queue.close()

def test_execution_id_is_idempotent_for_same_objective(tmp_path):
    queue = make_queue(tmp_path); first = queue.enqueue("same-id", "first"); second = queue.enqueue("same-id", "first")
    assert second.job_id == first.job_id; assert second.status == "queued"; assert second.attempts == 0; assert queue.store.status()["queued"] == 1; queue.close()

def test_execution_id_cannot_be_reused_for_different_objective(tmp_path):
    queue = make_queue(tmp_path); queue.enqueue("same-id", "first")
    try: queue.enqueue("same-id", "second")
    except ValueError as exc: assert "different objective" in str(exc)
    else: raise AssertionError("execution_id reuse with a different request must be rejected")
    queue.close()

def test_execution_id_is_idempotent_under_concurrent_queues(tmp_path):
    db_path = tmp_path / "runtime.db"; queues = [PersistentJobQueue(RuntimeStore(db_path)), PersistentJobQueue(RuntimeStore(db_path))]
    def enqueue(queue): return queue.enqueue("concurrent-id", "same objective")
    try:
        with ThreadPoolExecutor(max_workers=2) as executor: results = list(executor.map(enqueue, queues))
        assert [result.job_id for result in results] == ["concurrent-id", "concurrent-id"]; assert all(result.objective == "same objective" for result in results); assert queues[0].store.status()["queued"] == 1
    finally:
        for queue in queues: queue.close()

from aurelix_runtime.job_queue import PersistentJobQueue


def test_queue_claim_execute_and_recovery():
    queue = PersistentJobQueue()
    queue.enqueue("job-1", "objective")
    result = queue.execute("job-1")
    assert result.status == "awaiting_approval"
    assert queue.jobs["job-1"].status == "awaiting_approval"


def test_running_jobs_are_recoverable():
    queue = PersistentJobQueue()
    queue.enqueue("job-2", "objective")
    queue.claim("job-2")
    assert queue.jobs["job-2"].status == "running"
    assert queue.recover_running() == 1
    assert queue.jobs["job-2"].status == "queued"

import pytest

from aurelix_runtime.job_queue import PersistentJobQueue
from aurelix_runtime.service import RuntimeConfig, RuntimeService


def test_runtime_lifecycle_and_job_execution():
    queue = PersistentJobQueue()
    queue.enqueue("job-1", "objective")
    runtime = RuntimeService(queue, RuntimeConfig(tick_seconds=0.01))
    assert runtime.status == "stopped"
    runtime.start()
    assert runtime.status == "running"
    runtime.tick()
    assert queue.jobs["job-1"].status == "awaiting_approval"
    runtime.stop()
    assert runtime.status == "stopping"


def test_runtime_requires_start_before_tick():
    runtime = RuntimeService()
    with pytest.raises(RuntimeError):
        runtime.tick()

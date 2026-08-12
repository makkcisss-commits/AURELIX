from aurelix_runtime.scheduler import Scheduler, Schedule


def test_scheduler_tick_runs_queued_pipeline_job():
    scheduler = Scheduler()
    scheduler.add(Schedule("research", 1, "research_pipeline", {"objective": "test"}))
    job_id = scheduler.submit("research_pipeline", {"objective": "test"})
    processed = scheduler.tick()
    assert processed == [job_id]
    assert scheduler.queue.jobs[job_id].status == "awaiting_approval"


def test_scheduler_rejects_unapproved_job_kind():
    scheduler = Scheduler()
    try:
        scheduler.submit("arbitrary_action", {"objective": "test"})
    except PermissionError:
        return
    assert False, "unapproved job kind must be rejected"

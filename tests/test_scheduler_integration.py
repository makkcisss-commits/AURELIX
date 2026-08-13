from aurelix_runtime.scheduler import Scheduler, Schedule


def test_scheduler_tick_runs_complete_autonomy_job():
    scheduler = Scheduler()
    scheduler.add(Schedule("research", 1, "research_pipeline", {"objective": "test"}))
    job_id = scheduler.submit("research_pipeline", {"objective": "test"})
    processed = scheduler.tick()
    assert processed == [job_id]
    assert scheduler.queue.jobs[job_id].status == "completed"
    durable = scheduler.queue.store.get_result(job_id)
    assert durable["status"] == "awaiting_validation"
    assert durable["execution_id"] == job_id
    assert set(durable) >= {"execution_id", "status", "research", "academy", "knowledge", "innovation", "experiment", "evaluation", "opportunity", "business"}
    scheduler.queue.close()


def test_scheduler_persists_engine_state_in_the_same_runtime_store():
    scheduler = Scheduler()
    job_id = scheduler.submit("autonomy.run", {"objective": "persist me"})
    scheduler.tick()
    with scheduler.queue.store.lock:
        keys = {row[0] for row in scheduler.queue.store.db.execute("SELECT key FROM runtime_state WHERE key LIKE 'engine.%'").fetchall()}
    assert {"engine.knowledge", "engine.experiments", "engine.opportunities", "engine.audit"} <= keys
    assert scheduler.queue.store.get_result(job_id)["execution_id"] == job_id
    scheduler.queue.close()


def test_scheduler_rejects_unapproved_job_kind():
    scheduler = Scheduler()
    try:
        scheduler.submit("arbitrary_action", {"objective": "test"})
    except PermissionError:
        scheduler.queue.close()
        return
    scheduler.queue.close()
    assert False, "unapproved job kind must be rejected"

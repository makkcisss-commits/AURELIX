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


def test_scheduler_definitions_survive_restart_and_update_in_place(tmp_path):
    db_path = tmp_path / "scheduler.db"
    first = Scheduler(queue=__import__("aurelix_runtime.job_queue", fromlist=["PersistentJobQueue"]).PersistentJobQueue(store=__import__("aurelix_runtime.persistence", fromlist=["RuntimeStore"]).RuntimeStore(db_path)))
    first.add(Schedule("daily", 60, "system.cycle", {"objective": "one"}))
    first.add(Schedule("daily", 120, "system.cycle", {"objective": "two"}))
    first.queue.close()

    second = Scheduler(queue=__import__("aurelix_runtime.job_queue", fromlist=["PersistentJobQueue"]).PersistentJobQueue(store=__import__("aurelix_runtime.persistence", fromlist=["RuntimeStore"]).RuntimeStore(db_path)))
    assert second.schedules == [Schedule("daily", 120, "system.cycle", {"objective": "two"})]
    assert second.remove("daily") is True
    second.reload()
    assert second.schedules == []
    second.queue.close()

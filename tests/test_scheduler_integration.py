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
    from aurelix_runtime.job_queue import PersistentJobQueue
    from aurelix_runtime.persistence import RuntimeStore

    db_path = tmp_path / "scheduler.db"
    first = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    first.add(Schedule("daily", 60, "system.cycle", {"objective": "one"}))
    first.add(Schedule("daily", 120, "system.cycle", {"objective": "two"}))
    first.queue.close()

    second = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    assert second.schedules == [Schedule("daily", 120, "system.cycle", {"objective": "two"})]
    assert second.remove("daily") is True
    second.reload()
    assert second.schedules == []
    second.queue.close()


def test_scheduler_next_run_survives_restart_without_resetting_to_now(tmp_path):
    from aurelix_runtime.job_queue import PersistentJobQueue
    from aurelix_runtime.persistence import RuntimeStore

    db_path = tmp_path / "scheduler-due.db"
    first = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    first.add(Schedule("hourly", 3600, "system.cycle", {"objective": "due-time"}))
    original_due = first._next_run_at["hourly"]
    assert original_due - first._now() >= 3590
    first.queue.close()

    second = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    assert second._next_run_at["hourly"] == original_due
    second.queue.close()


def test_scheduler_overdue_schedule_is_coalesced_after_restart(tmp_path):
    from aurelix_runtime.job_queue import PersistentJobQueue
    from aurelix_runtime.persistence import RuntimeStore
    import time

    db_path = tmp_path / "scheduler-overdue.db"
    first = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    first.add(Schedule("missed", 60, "system.cycle", {"objective": "recover"}))
    with first.queue.store.lock, first.queue.store.db:
        first.queue.store.db.execute("UPDATE schedules SET next_run_at=? WHERE name=?", (time.time() - 120, "missed"))
    first.queue.close()

    second = Scheduler(queue=PersistentJobQueue(store=RuntimeStore(db_path)))
    assert second._next_run_at["missed"] < time.time()
    now = time.time()
    schedule = second.schedules[0]
    submitted = []
    second.submit = lambda kind, payload: submitted.append((kind, payload)) or "job"
    second.submit(schedule.job_kind, schedule.payload)
    second._persist_schedule(schedule, now + schedule.interval_seconds)
    assert submitted == [("system.cycle", {"objective": "recover"})]
    assert second._next_run_at["missed"] > now
    second.queue.close()

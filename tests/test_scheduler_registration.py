from aurelix_runtime.scheduler import Schedule, Scheduler


def test_schedule_registration_replaces_existing_identity():
    scheduler = Scheduler()
    try:
        scheduler.add(Schedule("economic-discovery", 900, "system.cycle", {"objective": "old"}))
        scheduler.add(Schedule("economic-discovery", 60, "system.cycle", {"objective": "new"}))

        assert len(scheduler.schedules) == 1
        assert scheduler.schedules[0] == Schedule(
            "economic-discovery", 60, "system.cycle", {"objective": "new"}
        )
    finally:
        scheduler.stop()

from aurelix_runtime.system import AurelixSystem


def test_system_cycle_schedule_is_singleton():
    system = AurelixSystem()
    try:
        system.schedule_system_cycle("default-autonomy", 900, "override objective")
        schedules = [s for s in system.scheduler.schedules if s.job_kind == "system.cycle"]
        assert len(schedules) == 1
        assert schedules[0].name == "default-autonomy"
        assert schedules[0].payload["objective"] == "override objective"
    finally:
        system.close()

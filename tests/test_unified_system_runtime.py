def test_system_scheduler_runs_cycle_on_shared_runtime(tmp_path):
    from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
    from aurelix_runtime.system import AurelixSystem

    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    calls = []
    system = AurelixSystem(
        runtime=runtime,
        cycle_handler=lambda objective: calls.append(objective),
        config=None,
    )
    try:
        system.schedule_system_cycle("test-cycle", 1, "maintain the system")
        system.start()
        system.tick()
        assert calls == ["maintain the system"]
        assert system.health()["system_cycle"] == "registered"
        assert system.health()["schedules"] == ["test-cycle"]
    finally:
        system.close()

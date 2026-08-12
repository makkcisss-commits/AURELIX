from aurelix_runtime.worker_supervisor import WorkerPolicy, WorkerState, WorkerSupervisor


def test_heartbeat_timeout_degrades_worker():
    sup = WorkerSupervisor()
    sup.register("research", WorkerPolicy(heartbeat_timeout_seconds=10))
    sup.start("research")
    record = sup.workers["research"]
    state = sup.health_check("research", now=record.last_heartbeat + 11)
    assert state == WorkerState.DEGRADED


def test_failure_opens_circuit_after_threshold():
    sup = WorkerSupervisor()
    sup.register("academy", WorkerPolicy(max_failures=2))
    sup.start("academy")
    sup.failure("academy", "provider unavailable")
    assert sup.workers["academy"].state == WorkerState.DEGRADED
    sup.failure("academy", "provider unavailable")
    assert sup.workers["academy"].state == WorkerState.OPEN


def test_success_resets_failure_and_retry_state():
    sup = WorkerSupervisor()
    sup.register("knowledge", WorkerPolicy())
    sup.start("knowledge")
    sup.failure("knowledge", "temporary")
    sup.record_retry("knowledge")
    sup.success("knowledge")
    record = sup.workers["knowledge"]
    assert record.state == WorkerState.RUNNING
    assert record.failures == 0
    assert record.retries == 0


def test_open_circuit_can_cool_down():
    sup = WorkerSupervisor()
    sup.register("innovation", WorkerPolicy(max_failures=1, cooldown_seconds=5))
    sup.start("innovation")
    sup.failure("innovation", "crash")
    opened_at = sup.workers["innovation"].opened_at
    assert opened_at is not None
    assert sup.health_check("innovation", now=opened_at + 6) == WorkerState.DEGRADED

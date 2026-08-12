from aurelix_runtime.observability import RuntimeHealth


def test_health_distinguishes_liveness_and_readiness():
    health = RuntimeHealth()
    assert health.live() is True
    assert health.ready(False) is False
    assert health.ready(True) is True


def test_metrics_snapshot_is_serializable():
    health = RuntimeHealth()
    health.metrics.ticks = 3
    health.metrics.heartbeats = 3
    snapshot = health.snapshot(True)
    assert snapshot["live"] is True
    assert snapshot["ready"] is True
    assert snapshot["metrics"]["ticks"] == 3

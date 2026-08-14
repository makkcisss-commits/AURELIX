from aurelix_core.governor import Governor
from aurelix_runtime.orchestrator import Capability, Orchestrator
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_full_orchestrator_governor_runtime_queue_worker_audit_restart(tmp_path):
    db = tmp_path / "aurelix.db"
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(db), heartbeat_seconds=2.0))
    try:
        orchestrator = Orchestrator(governor=Governor(), runtime=runtime)
        seen = []
        orchestrator.register(Capability("system.junction", lambda payload: seen.append(payload) or {"ok": True, "worker_result": payload["objective"].upper()}))
        job_id = orchestrator.submit(capability="system.junction", payload={"objective": "operate"})
        queued = runtime.store.get(job_id)
        assert queued is not None and queued.status == "queued"
        assert orchestrator.run_once() is True
        assert seen == [{"objective": "operate"}]
        completed = runtime.store.get(job_id)
        assert completed is not None and completed.status == "completed"
        assert runtime.store.get_result(job_id) == {"ok": True, "worker_result": "OPERATE"}
        audit = runtime.store.audit_summary(limit=20)["recent"]
        event_types = [event["event_type"] for event in audit if event["job_id"] == job_id]
        assert "job.queued" in event_types
        assert "job.completed" in event_types
    finally:
        runtime.close()

    restarted = AurelixRuntime(RuntimeConfig(database_path=str(db), heartbeat_seconds=2.0))
    try:
        assert restarted.store.get(job_id).status == "completed"
        assert restarted.store.get_result(job_id) == {"ok": True, "worker_result": "OPERATE"}
        assert restarted.run_once() is False
    finally:
        restarted.close()


def test_governor_blocks_unsafe_work_before_queue(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    try:
        orchestrator = Orchestrator(governor=Governor(), runtime=runtime)
        orchestrator.register(Capability("unsafe", lambda payload: {"should": "never run"}))
        try:
            orchestrator.submit(capability="unsafe", payload={"objective": "blocked"}, requires_capital=True)
        except PermissionError:
            pass
        else:
            raise AssertionError("Governor must block owner-gated work before queueing")
        assert runtime.store.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
    finally:
        runtime.close()

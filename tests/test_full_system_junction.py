from aurelix_core.audit import AuditLog
from aurelix_core.governor import Governor
from aurelix_runtime.orchestrator import Capability, Orchestrator
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_full_orchestrator_governor_runtime_queue_worker_audit_junction(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    governor_audit = AuditLog()
    governor = Governor(audit=governor_audit)
    seen = []

    try:
        orchestrator = Orchestrator(governor=governor, runtime=runtime)
        orchestrator.register(
            Capability(
                "unit",
                lambda payload: seen.append(payload) or {"ok": True, "echo": payload["objective"]},
                read_only=True,
            )
        )

        job_id = orchestrator.submit(capability="unit", payload={"objective": "full-junction"})

        queued = runtime.store.get(job_id)
        assert queued is not None
        assert queued.status == "queued"
        assert any(event.event_type == "job.queued" and event.job_id == job_id for event in runtime.store.audit_summary(20)["recent"])

        assert orchestrator.run_once() is True

        completed = runtime.store.get(job_id)
        assert completed is not None
        assert completed.status == "completed"
        assert runtime.store.get_result(job_id) == {"ok": True, "echo": "full-junction"}
        assert seen == [{"objective": "full-junction"}]

        governor_events = governor_audit.all()
        assert len(governor_events) == 0 or all(event.event_type != "decision.evaluated" for event in governor_events)
        runtime_events = runtime.store.audit_summary(20)["recent"]
        assert any(event["event_type"] == "job.completed" and event["job_id"] == job_id for event in runtime_events)
    finally:
        runtime.close()

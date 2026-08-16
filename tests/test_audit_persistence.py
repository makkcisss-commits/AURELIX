from aurelix_core.audit import AuditEvent, AuditLog
from aurelix_runtime.persistence import RuntimeStore


def test_audit_log_can_persist_events_to_runtime_store(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    audit = AuditLog(sink=store.record_audit)

    event = AuditEvent(
        event_type="decision.evaluated",
        actor_id="agent",
        subject_id="request-1",
        outcome="approved",
        metadata={"action": "research"},
    )
    audit.append(event)

    persisted = store.audit_summary(10)["recent"]
    assert len(persisted) == 1
    assert persisted[0]["event_type"] == event.event_type
    assert persisted[0]["job_id"] == event.subject_id
    assert persisted[0]["payload"]["event_id"] == event.event_id

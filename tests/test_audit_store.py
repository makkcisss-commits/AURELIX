from pathlib import Path

from aurelix_core.audit import AuditEvent
from aurelix_core.audit_store import AuditStore


def test_audit_store_appends_and_reads_events(tmp_path: Path) -> None:
    store = AuditStore(tmp_path / "audit.jsonl")
    event = AuditEvent(
        event_type="test.event",
        actor_id="agent-1",
        subject_id="task-1",
        outcome="success",
    )

    store.append(event)
    store.append(
        AuditEvent(
            event_type="test.event.2",
            actor_id="agent-1",
            subject_id="task-2",
            outcome="blocked",
        )
    )

    records = store.read_all()
    assert len(records) == 2
    assert records[0]["event_type"] == "test.event"
    assert records[1]["outcome"] == "blocked"


def test_audit_store_is_append_only_from_api(tmp_path: Path) -> None:
    store = AuditStore(tmp_path / "audit.jsonl")
    store.append(
        AuditEvent(
            event_type="first",
            actor_id="owner",
            subject_id="system",
            outcome="recorded",
        )
    )

    assert store.read_all()[0]["event_type"] == "first"

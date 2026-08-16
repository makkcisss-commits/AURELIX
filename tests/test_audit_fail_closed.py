import pytest

from aurelix_core.audit import AuditEvent, AuditLog


def test_audit_sink_failure_does_not_report_success():
    def unavailable_sink(*_args, **_kwargs):
        raise OSError("audit store unavailable")

    audit = AuditLog(sink=unavailable_sink)
    with pytest.raises(OSError, match="audit store unavailable"):
        audit.append(
            AuditEvent(
                event_type="decision.evaluated",
                actor_id="agent",
                subject_id="request-1",
                outcome="approved",
            )
        )
    assert audit.all() == ()

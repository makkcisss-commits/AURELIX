import pytest

from aurelix_core.audit import AuditLog
from aurelix_core.identity import Identity, IdentityStatus, register_secret
from aurelix_core.private_api import ApiDenied, PrivateApi


def test_private_api_authenticates_and_dispatches_registered_operation() -> None:
    audit = AuditLog()
    api = PrivateApi(audit)
    api.register("system.status", lambda principal, payload: {"actor": principal.identity.id, "ok": True})

    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")
    result = api.call(identity, credential, "secret", "system.status")

    assert result == {"actor": "owner", "ok": True}
    assert audit.all()[-1].event_type == "api.operation_completed"


def test_private_api_rejects_bad_credentials_without_dispatch() -> None:
    audit = AuditLog()
    api = PrivateApi(audit)
    calls: list[object] = []
    api.register("system.status", lambda principal, payload: calls.append(payload) or "must-not-run")

    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")

    with pytest.raises(ApiDenied):
        api.call(identity, credential, "wrong", "system.status", {"sensitive": True})

    assert calls == []
    assert audit.all()[-1].event_type == "api.authentication_denied"


def test_private_api_rejects_missing_secret_without_dispatch() -> None:
    audit = AuditLog()
    api = PrivateApi(audit)
    calls: list[object] = []
    api.register("system.status", lambda principal, payload: calls.append(payload) or "must-not-run")

    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")

    with pytest.raises(ApiDenied):
        api.call(identity, credential, "", "system.status")

    assert calls == []
    assert audit.all()[-1].event_type == "api.authentication_denied"


def test_private_api_rejects_revoked_identity_without_dispatch() -> None:
    audit = AuditLog()
    api = PrivateApi(audit)
    calls: list[object] = []
    api.register("system.status", lambda principal, payload: calls.append(payload) or "must-not-run")

    identity = Identity("owner", "owner", IdentityStatus.REVOKED)
    credential = register_secret(identity.id, "secret")

    with pytest.raises(ApiDenied):
        api.call(identity, credential, "secret", "system.status")

    assert calls == []
    assert audit.all()[-1].event_type == "api.authentication_denied"


def test_private_api_rejects_unknown_operation() -> None:
    audit = AuditLog()
    api = PrivateApi(audit)
    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")

    with pytest.raises(ApiDenied):
        api.call(identity, credential, "secret", "does.not.exist")

    assert audit.all()[-1].event_type == "api.operation_denied"

from aurelix_core.audit import AuditLog
from aurelix_core.identity import Identity, register_secret
from aurelix_core.private_api import PrivateApi
from aurelix_core.transport import PrivateTransport


def test_transport_returns_success_for_authenticated_registered_operation() -> None:
    api = PrivateApi(AuditLog())
    api.register("system.status", lambda principal, payload: {"ok": True})
    transport = PrivateTransport(api)
    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")

    response = transport.handle(identity, credential, "secret", "system.status")
    assert response.status_code == 200
    assert response.body["ok"] is True


def test_transport_returns_generic_forbidden_response() -> None:
    api = PrivateApi(AuditLog())
    api.register("system.status", lambda principal, payload: {"ok": True})
    transport = PrivateTransport(api)
    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")

    response = transport.handle(identity, credential, "wrong", "system.status")
    assert response.status_code == 403
    assert response.body == {"ok": False, "error": "forbidden"}

import pytest

import aurelix_core.server as server
from aurelix_core.authorization import AuthorizationDenied
from aurelix_core.identity import Identity, register_secret


def test_protected_actions_reject_invalid_secret(monkeypatch):
    monkeypatch.setattr(server, "_identity", Identity("owner", "owner"))
    monkeypatch.setattr(server, "_credential", register_secret("owner", "real-secret"))

    with pytest.raises(Exception) as exc:
        server.require_owner("wrong-secret")

    assert getattr(exc.value, "status_code", None) == 401


def test_action_scope_is_explicit():
    policy = server.owner_read_only_policy("owner")
    identity = Identity("owner", "owner")
    policy.authorize(identity, "actions", "research.execute", "private")
    policy.authorize(identity, "actions", "objectives.submit", "private")
    policy.authorize(identity, "actions", "economic.outcome.record", "private")

    with pytest.raises(AuthorizationDenied):
        policy.authorize(identity, "actions", "shell.execute", "private")

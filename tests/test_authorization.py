import pytest

from aurelix_core.authorization import AuthorizationDenied, Capability, AuthorizationPolicy, owner_read_only_policy
from aurelix_core.identity import Identity, IdentityStatus


def test_exact_resource_operation_scope_is_allowed() -> None:
    identity = Identity("owner", "owner")
    owner_read_only_policy("owner").authorize(identity, "control", "snapshot", "private")


def test_missing_scope_fails_closed() -> None:
    identity = Identity("owner", "owner")
    with pytest.raises(AuthorizationDenied):
        owner_read_only_policy("owner").authorize(identity, "control", "snapshot", "")


def test_wrong_resource_is_denied() -> None:
    identity = Identity("owner", "owner")
    with pytest.raises(AuthorizationDenied):
        owner_read_only_policy("owner").authorize(identity, "secrets", "read", "private")


def test_wrong_operation_is_denied() -> None:
    identity = Identity("owner", "owner")
    with pytest.raises(AuthorizationDenied):
        owner_read_only_policy("owner").authorize(identity, "control", "write", "private")


def test_other_identity_gets_no_owner_capabilities() -> None:
    identity = Identity("operator", "operator")
    with pytest.raises(AuthorizationDenied):
        owner_read_only_policy("owner").authorize(identity, "control", "snapshot", "private")


def test_revoked_identity_is_denied_even_with_capability() -> None:
    identity = Identity("owner", "owner", IdentityStatus.REVOKED)
    policy = AuthorizationPolicy({"owner": frozenset({Capability("control", "snapshot", "private")})})
    with pytest.raises(AuthorizationDenied):
        policy.authorize(identity, "control", "snapshot", "private")


def test_wildcard_is_not_implicit() -> None:
    identity = Identity("owner", "owner")
    policy = owner_read_only_policy("owner")
    with pytest.raises(AuthorizationDenied):
        policy.authorize(identity, "control", "anything", "private")

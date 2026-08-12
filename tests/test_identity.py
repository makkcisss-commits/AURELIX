import pytest

from aurelix_core.identity import (
    AuthenticationError,
    Identity,
    IdentityStatus,
    authenticate,
    register_secret,
)


def test_active_identity_authenticates_with_matching_secret() -> None:
    identity = Identity("owner", "owner")
    record = register_secret(identity.id, "correct-secret")
    assert authenticate(identity, record, "correct-secret") == identity


def test_wrong_secret_is_rejected() -> None:
    identity = Identity("owner", "owner")
    record = register_secret(identity.id, "correct-secret")
    with pytest.raises(AuthenticationError):
        authenticate(identity, record, "wrong-secret")


def test_revoked_identity_is_rejected() -> None:
    identity = Identity("agent-1", "research", IdentityStatus.REVOKED)
    record = register_secret(identity.id, "secret")
    with pytest.raises(AuthenticationError):
        authenticate(identity, record, "secret")


def test_credential_cannot_be_reused_for_another_identity() -> None:
    owner = Identity("owner", "owner")
    other = Identity("other", "operator")
    record = register_secret(owner.id, "secret")
    with pytest.raises(AuthenticationError):
        authenticate(other, record, "secret")

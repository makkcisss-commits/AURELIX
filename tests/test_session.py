from datetime import timedelta

from aurelix_core.session import SessionStore


def test_session_is_created_and_validated() -> None:
    store = SessionStore(ttl_minutes=30)
    session = store.create("owner")
    assert store.validate(session.token) == session


def test_session_can_be_revoked() -> None:
    store = SessionStore()
    session = store.create("owner")
    store.revoke(session.token)
    assert store.validate(session.token) is None

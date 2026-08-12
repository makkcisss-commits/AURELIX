from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import secrets


@dataclass(frozen=True)
class Session:
    token: str
    owner_id: str
    expires_at: datetime


class SessionStore:
    """Small in-memory session store for the V1 application boundary.

    Production deployments should replace this with a durable, encrypted
    server-side session store or an identity provider. Tokens are never
    persisted in source control and are never returned by dashboard reads.
    """

    def __init__(self, ttl_minutes: int = 30) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._sessions: dict[str, Session] = {}

    def create(self, owner_id: str) -> Session:
        token = secrets.token_urlsafe(32)
        session = Session(token, owner_id, datetime.now(timezone.utc) + self._ttl)
        self._sessions[token] = session
        return session

    def validate(self, token: str | None) -> Session | None:
        if not token:
            return None
        session = self._sessions.get(token)
        if session is None or session.expires_at <= datetime.now(timezone.utc):
            if session is not None:
                self._sessions.pop(token, None)
            return None
        return session

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)

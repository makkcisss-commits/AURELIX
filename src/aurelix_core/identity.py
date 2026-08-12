from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import hmac
import secrets


class IdentityStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    DISABLED = "disabled"


class AuthenticationError(Exception):
    """Raised when a presented credential cannot authenticate an identity."""


@dataclass(frozen=True)
class Identity:
    id: str
    role: str
    status: IdentityStatus = IdentityStatus.ACTIVE


@dataclass(frozen=True)
class CredentialRecord:
    identity_id: str
    salt: bytes
    digest: bytes


def issue_secret() -> str:
    return secrets.token_urlsafe(32)


def register_secret(identity_id: str, secret: str) -> CredentialRecord:
    if not identity_id or not secret:
        raise ValueError("identity_id and secret are required")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(secret.encode(), salt=salt, n=2**14, r=8, p=1)
    return CredentialRecord(identity_id, salt, digest)


def authenticate(identity: Identity, record: CredentialRecord, secret: str) -> Identity:
    if identity.status is not IdentityStatus.ACTIVE:
        raise AuthenticationError("identity is not active")
    if record.identity_id != identity.id:
        raise AuthenticationError("credential identity mismatch")
    candidate = hashlib.scrypt(secret.encode(), salt=record.salt, n=2**14, r=8, p=1)
    if not hmac.compare_digest(candidate, record.digest):
        raise AuthenticationError("invalid credential")
    return identity

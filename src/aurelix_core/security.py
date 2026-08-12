from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets
import time


@dataclass(frozen=True)
class SecretHash:
    salt: str
    digest: str


def hash_secret(secret: str, salt: str | None = None) -> SecretHash:
    if not secret:
        raise ValueError("secret must not be empty")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(
        secret.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1
    ).hex()
    return SecretHash(salt, digest)


def verify_secret(secret: str, stored: SecretHash) -> bool:
    if not secret:
        return False
    candidate = hashlib.scrypt(
        secret.encode(), salt=bytes.fromhex(stored.salt), n=2**14, r=8, p=1
    ).hex()
    return hmac.compare_digest(candidate, stored.digest)


@dataclass
class AttemptLimiter:
    max_attempts: int = 5
    window_seconds: int = 300
    _attempts: dict[str, list[float]] | None = None

    def __post_init__(self) -> None:
        self._attempts = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        attempts = self._attempts.setdefault(key, [])
        attempts[:] = [stamp for stamp in attempts if now - stamp < self.window_seconds]
        if len(attempts) >= self.max_attempts:
            return False
        attempts.append(now)
        return True

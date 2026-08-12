from aurelix_core.security import AttemptLimiter, hash_secret, verify_secret


def test_secret_hash_is_not_plaintext_and_verifies() -> None:
    stored = hash_secret("strong-secret")
    assert stored.digest != "strong-secret"
    assert verify_secret("strong-secret", stored)
    assert not verify_secret("wrong-secret", stored)


def test_attempt_limiter_blocks_after_threshold() -> None:
    limiter = AttemptLimiter(max_attempts=2, window_seconds=300)
    assert limiter.allow("client")
    assert limiter.allow("client")
    assert not limiter.allow("client")

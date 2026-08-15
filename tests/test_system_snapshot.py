from aurelix_core.system_snapshot import SystemSnapshot


def test_public_snapshot_is_conservative_by_default() -> None:
    snapshot = SystemSnapshot()
    assert snapshot.public() == {
        "system": "UNVERIFIED",
        "governor": "UNVERIFIED",
        "policy": "UNVERIFIED",
        "audit": "UNVERIFIED",
        "api": "UNVERIFIED",
        "execution": "UNVERIFIED",
        "budget": "UNVERIFIED",
        "breaker": "UNVERIFIED",
    }


def test_explicit_verified_state_is_preserved() -> None:
    snapshot = SystemSnapshot(
        system="HEALTHY",
        governor="OPERATIONAL",
        policy="ACTIVE",
        audit="RECORDING",
        api="PROTECTED",
        execution="GUARDED",
        budget="ACTIVE",
        breaker="READY",
    )
    assert snapshot.public()["system"] == "HEALTHY"
    assert snapshot.public()["governor"] == "OPERATIONAL"

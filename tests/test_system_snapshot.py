from aurelix_core.system_snapshot import SystemSnapshot


def test_public_snapshot_contains_only_dashboard_state() -> None:
    snapshot = SystemSnapshot()
    assert snapshot.public() == {
        "system": "HEALTHY",
        "governor": "OPERATIONAL",
        "policy": "ACTIVE",
        "audit": "RECORDING",
        "api": "PROTECTED",
        "execution": "GUARDED",
        "budget": "ACTIVE",
        "breaker": "READY",
    }

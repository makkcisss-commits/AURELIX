from pathlib import Path

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_runtime_bootstrap_persists_heartbeat_and_reports_status(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))

    assert runtime.store.status()["heartbeat"] == "never"

    runtime.store.heartbeat()

    status = runtime.store.status()
    assert status["heartbeat"] != "never"
    assert status["queued"] == 0
    assert status["running"] == 0
    assert status["succeeded"] == 0
    assert status["failed"] == 0
    assert (tmp_path / "runtime.db").exists()

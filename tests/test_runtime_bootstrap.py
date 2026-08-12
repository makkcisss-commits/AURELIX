from pathlib import Path

from aurelix_runtime.config import RuntimeConfig
from aurelix_runtime.runtime import AurelixRuntime


def test_runtime_bootstrap_persists_and_reads_heartbeat(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))

    assert runtime.health() == "ok"
    assert runtime.heartbeat() is None

    runtime.beat("ci-bootstrap")

    assert runtime.heartbeat() == "ci-bootstrap"
    assert (tmp_path / "runtime.db").exists()

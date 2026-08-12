from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_runtime_bootstrap_creates_durable_store(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    assert runtime.store.status()["heartbeat"] == "never"
    runtime.store.heartbeat()
    assert runtime.store.status()["heartbeat"] != "never"

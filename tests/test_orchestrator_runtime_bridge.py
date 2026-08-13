from aurelix_core.governor import Governor
from aurelix_runtime.orchestrator import Capability, Orchestrator
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_orchestrator_uses_shared_runtime_queue(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    try:
        orchestrator = Orchestrator(governor=Governor(), runtime=runtime)
        seen = []
        orchestrator.register(Capability("unit", lambda payload: seen.append(payload) or {"ok": True}, read_only=True))
        job_id = orchestrator.submit(capability="unit", payload={"objective": "bridge"})
        assert runtime.store.get(job_id).status == "queued"
        assert orchestrator.run_once() is True
        assert seen == [{"objective": "bridge"}]
        assert runtime.store.get(job_id).status == "completed"
        assert runtime.store.get_result(job_id) == {"ok": True}
    finally:
        runtime.close()


def test_orchestrator_rejects_ungoverned_runtime_submission(tmp_path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    try:
        orchestrator = Orchestrator(governor=Governor(), runtime=runtime)
        orchestrator.register(Capability("capital", lambda payload: None))
        try:
            orchestrator.submit(capability="capital", payload={}, requires_capital=True)
        except PermissionError:
            pass
        else:
            raise AssertionError("owner-gated work must not enter the shared runtime")
        assert runtime.store.db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0
    finally:
        runtime.close()

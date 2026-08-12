from pathlib import Path

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_runtime_retries_before_terminal_failure(tmp_path: Path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db"), max_attempts=2))
    runtime.register("failing", lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
    job_id = runtime.submit("failing", {})
    assert runtime.run_once() is True
    assert runtime.store.status()["queued"] == 1
    assert runtime.run_once() is True
    assert runtime.store.status()["failed"] == 1
    rows = runtime.store.db.execute(
        "SELECT event_type FROM audit WHERE subject=? ORDER BY created_at", (job_id,)
    ).fetchall()
    assert [row[0] for row in rows] == ["job.queued", "job.retry", "job.failed"]

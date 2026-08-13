from pathlib import Path

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def test_runtime_executes_registered_governed_pipeline(tmp_path: Path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    runtime.register_pipeline()
    job_id = runtime.submit("pipeline.run", {"objective": "integration objective"})
    assert runtime.run_once() is True
    status = runtime.store.status()
    assert status["succeeded"] == 1
    assert status["failed"] == 0
    # The queued job is durable and the canonical audit trail records its completion.
    rows = runtime.store.db.execute(
        "SELECT event_type, json_extract(payload, '$.outcome') AS outcome, job_id AS subject "
        "FROM audit_events WHERE job_id=? ORDER BY created_at",
        (job_id,),
    ).fetchall()
    assert [row["event_type"] for row in rows] == ["job.queued", "job.completed"]

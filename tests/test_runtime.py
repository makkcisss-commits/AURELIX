from pathlib import Path

import pytest

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from aurelix_runtime.scheduler import Schedule, Scheduler


def test_runtime_persists_and_runs_jobs(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    seen: list[dict[str, str]] = []
    runtime.register("academy.maintenance", seen.append)
    runtime.submit("academy.maintenance", {"mode": "scan"})
    assert runtime.run_once()
    assert seen == [{"mode": "scan"}]
    assert runtime.store.status()["succeeded"] == 1


def test_scheduler_only_enqueues_registered_work(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    runtime.register("research.heartbeat", lambda _: None)
    scheduler = Scheduler(runtime.submit)
    scheduler.add(Schedule("research", 1, "research.heartbeat", {}))
    scheduler.submit("research.heartbeat", {})
    assert runtime.run_once()


def test_runtime_denies_high_risk_submission_before_enqueue(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    calls: list[dict[str, str]] = []
    runtime.register("sensitive.action", calls.append)

    with pytest.raises(PermissionError):
        runtime.submit("sensitive.action", {"secret": "no"}, risk=8)

    assert calls == []
    assert runtime.store.status()["queued"] == 0
    assert runtime.store.audit_summary()["recent"][0]["event_type"] == "job.denied"


def test_runtime_denies_capital_and_production_changes_without_owner_review(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    runtime.register("sensitive.action", lambda _: None)

    with pytest.raises(PermissionError):
        runtime.submit("sensitive.action", requires_capital=True)
    with pytest.raises(PermissionError):
        runtime.submit("sensitive.action", production_change=True)

    assert runtime.store.status()["queued"] == 0

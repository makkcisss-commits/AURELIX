from __future__ import annotations

from pathlib import Path

from aurelix_runtime.integrated_engines import Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def make_runtime(tmp_path: Path) -> AurelixRuntime:
    return AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db"), heartbeat_seconds=2.0, worker_poll_seconds=0.01, max_attempts=2))


def test_experiment_is_executed_by_runtime_and_evaluated(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    calls = {"count": 0}
    try:
        experiment = Experiment("exp-real-1", "executor produces a measurable score", [{"metric": "score", "operator": ">=", "target": 0.5}])

        def executor(_experiment: Experiment):
            calls["count"] += 1
            return [{"score": 0.75}]

        runtime.register_experiment_runner(executor)
        job_id = runtime.submit_experiment(experiment)
        assert runtime.run_once() is True
        assert runtime.store.get(job_id).status == "completed"
        persisted = runtime.get_experiment(experiment.id)
        assert persisted.status == "complete"
        assert persisted.result["passed"] is True
        assert persisted.result["metrics"]["score"] == 0.75
        assert calls["count"] == 1
    finally:
        runtime.close()


def test_missing_measurement_does_not_validate_experiment(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    try:
        experiment = Experiment("exp-real-2", "measurement is unavailable", [{"metric": "score", "operator": ">=", "target": 0.5}])
        runtime.register_experiment_runner(lambda _experiment: [])
        job_id = runtime.submit_experiment(experiment)
        assert runtime.run_once() is True
        assert runtime.store.get(job_id).status == "completed"
        persisted = runtime.get_experiment(experiment.id)
        assert persisted.status == "awaiting_measurement"
        assert persisted.result is None
    finally:
        runtime.close()


def test_submit_is_idempotent_for_same_experiment(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    try:
        experiment = Experiment("exp-idempotent", "one durable execution", [{"metric": "score", "operator": ">=", "target": 1.0}])
        runtime.register_experiment_runner(lambda _experiment: [{"score": 1.0}])
        first = runtime.submit_experiment(experiment)
        second = runtime.submit_experiment(experiment)
        assert first == second
        assert runtime.run_once() is True
        third = runtime.submit_experiment(experiment)
        assert third == first
    finally:
        runtime.close()

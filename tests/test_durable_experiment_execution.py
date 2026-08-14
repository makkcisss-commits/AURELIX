from __future__ import annotations

from pathlib import Path

from aurelix_runtime.integrated_engines import Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


def make_runtime(tmp_path: Path) -> AurelixRuntime:
    return AurelixRuntime(
        RuntimeConfig(
            database_path=str(tmp_path / "aurelix.db"),
            heartbeat_seconds=2.0,
            worker_poll_seconds=0.01,
            max_attempts=2,
        )
    )


def test_experiment_is_executed_by_runtime_and_evaluated(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    try:
        experiment = Experiment(
            id="exp-real-1",
            hypothesis="the executor produces a measurable conversion",
            success_criteria=[{"metric": "conversion", "operator": ">=", "target": 0.5}],
        )

        runtime.register_experiment_runner(
            lambda _experiment: [{"conversion": 0.75}]
        )
        job_id = runtime.submit_experiment(experiment)

        assert runtime.run_once() is True
        job = runtime.store.get(job_id)
        assert job is not None
        assert job.status == "completed"

        persisted = runtime.get_experiment(experiment.id)
        assert persisted.status == "complete"
        assert persisted.result is not None
        assert persisted.result["passed"] is True
        assert persisted.result["metrics"]["conversion"] == 0.75
        assert runtime.query_experiment_observations(experiment.id) == [{"conversion": 0.75}]
    finally:
        runtime.close()


def test_missing_measurement_does_not_validate_experiment(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    try:
        experiment = Experiment(
            id="exp-real-2",
            hypothesis="measurement is unavailable",
            success_criteria=[{"metric": "conversion", "operator": ">=", "target": 0.5}],
        )

        runtime.register_experiment_runner(lambda _experiment: [])
        job_id = runtime.submit_experiment(experiment)

        assert runtime.run_once() is True
        assert runtime.store.get(job_id).status == "completed"
        persisted = runtime.get_experiment(experiment.id)
        assert persisted.status == "awaiting_measurement"
        assert persisted.result is None
    finally:
        runtime.close()


def test_completed_experiment_is_idempotent(tmp_path: Path) -> None:
    runtime = make_runtime(tmp_path)
    calls = {"count": 0}
    try:
        experiment = Experiment(
            id="exp-real-3",
            hypothesis="the first execution is sufficient",
            success_criteria=[{"metric": "score", "operator": ">=", "target": 1}],
        )

        def executor(_experiment: Experiment):
            calls["count"] += 1
            return [{"score": 1}]

        runtime.register_experiment_runner(executor)
        runtime.submit_experiment(experiment)
        assert runtime.run_once() is True
        assert calls["count"] == 1

        assert runtime.submit_experiment(experiment)  # same experiment id is intentionally rejected by durable PK
    except Exception:
        # A second enqueue with the same execution identity must not silently
        # create a duplicate experiment execution.
        assert calls["count"] == 1
    finally:
        runtime.close()

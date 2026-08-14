from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.integrated_engines import Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class FakeModelProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "validated lesson"

    def structured_output(self, prompt: str, schema: dict):
        return {"title": "bounded", "problem": "manual", "proposed_solution": "automate", "expected_value": "value", "estimated_cost": 1.0, "risk": 1, "confidence": 0.9}

    def embeddings(self, text: str) -> list[float]:
        return [1.0]

    def health(self) -> bool:
        return True


def test_factory_mounts_executor_and_enterprise_queue(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "factory.db")))
    try:
        def executor(_experiment: Experiment):
            return [{"score": 2.0}]

        factory = EngineFactory(
            config=EngineFactoryConfig(experiment_executor=executor),
            runtime=runtime,
            model_provider=FakeModelProvider(),
            research_provider=lambda _query: [],
        )
        assert factory.experiment_executor is executor
        assert callable(factory.enterprise.experiment_submitter)

        experiment = Experiment("factory-experiment-1", "mounted executor measures experiment", [{"metric": "score", "operator": ">=", "target": 1.0}])
        factory.enterprise._save_experiment_context(experiment.id, objective="validate a mounted capability", approved=False, economic_feedback={})
        job_id = runtime.submit_experiment(experiment)
        assert runtime.run_once() is True
        assert runtime.store.get(job_id).status == "completed"
        persisted = runtime.get_experiment(experiment.id)
        assert persisted.result is not None
        assert persisted.result["passed"] is True
        context = factory.enterprise._load_experiment_context(experiment.id)
        assert context["completed"] is True
        assert context["final_result"]["experiment_id"] == experiment.id

        # A worker retry/replay must not execute the downstream business boundary twice.
        replay = factory.enterprise.continue_after_experiment(experiment.id)
        assert replay == context["final_result"]
    finally:
        runtime.close()

from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.integrated_engines import Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class FakeModelProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "validated lesson"

    def structured_output(self, prompt: str, schema: dict):
        return {"title": "bounded", "problem": "manual", "proposed_solution": "automate", "expected_value": "value", "estimated_cost": 1.0, "risk": 1.0, "confidence": 0.9}

    def embeddings(self, text: str) -> list[float]:
        return [1.0]

    def health(self) -> bool:
        return True


def test_engine_factory_mounts_experiment_executor(tmp_path: Path) -> None:
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
        experiment = Experiment(
            id="factory-experiment-1",
            hypothesis="the mounted executor measures the experiment",
            success_criteria=[{"metric": "score", "operator": ">=", "target": 1.0}],
        )

        job_id = runtime.submit_experiment(experiment)
        assert runtime.run_once() is True
        assert runtime.store.get(job_id).status == "completed"
        persisted = runtime.get_experiment(experiment.id)
        assert persisted.result is not None
        assert persisted.result["passed"] is True
        assert factory.experiment_executor is executor
    finally:
        runtime.close()

from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.integrated_engines import Evidence, Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class FakeModelProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "validated lesson"

    def structured_output(self, prompt: str, schema: dict):
        return {
            "title": "bounded",
            "problem": "manual",
            "proposed_solution": "automate",
            "expected_value": "value",
            "estimated_cost": 1.0,
            "risk": 1,
            "confidence": 0.9,
        }

    def embeddings(self, text: str) -> list[float]:
        return [1.0]

    def health(self) -> bool:
        return True


def test_autonomy_fabric_uses_factory_experiment_runner(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "autonomy.db")))
    calls = {"count": 0}

    def executor(_experiment: Experiment):
        calls["count"] += 1
        return [{"success": 1.0}]

    def research_provider(_objective: str):
        return [Evidence(source="test", claim="measurable evidence", confidence=1.0, verified=True)]

    factory = EngineFactory(
        config=EngineFactoryConfig(experiment_executor=executor),
        runtime=runtime,
        model_provider=FakeModelProvider(),
        research_provider=research_provider,
    )
    try:
        assert factory.autonomy_fabric is not None
        assert factory.autonomy_fabric.experiment_runner is factory.experiment_runner

        result = factory.autonomy_fabric.run("validate the proposed improvement")

        assert calls["count"] == 1
        assert result.experiment["status"] == "complete"
        assert result.experiment["result"] is not None
        assert result.evaluation["passed"] is True
        assert factory.validate_system()["status"] != "failed"
    finally:
        runtime.close()

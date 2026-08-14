from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.integrated_engines import Experiment
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class ModelProvider:
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "lesson"

    def structured_output(self, prompt: str, schema: dict):
        return {"title": "bounded", "problem": "manual", "proposed_solution": "automate", "expected_value": "value", "estimated_cost": 1.0, "risk": 1.0, "confidence": 0.9}

    def embeddings(self, text: str) -> list[float]:
        return [1.0]

    def health(self) -> bool:
        return True


def build_factory(tmp_path: Path, executor=None) -> EngineFactory:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "diagnostics.db")))
    return EngineFactory(
        config=EngineFactoryConfig(experiment_executor=executor),
        runtime=runtime,
        model_provider=ModelProvider(),
        research_provider=lambda _query: [],
    )


def test_diagnostics_fail_closed_without_experiment_executor(tmp_path: Path) -> None:
    factory = build_factory(tmp_path)
    try:
        report = factory.diagnose()
        check = next(item for item in report["checks"] if item["name"] == "experiment_execution")
        assert check["status"] == "failed"
        assert check["evidence"]["validation_allowed"] is False
    finally:
        factory.runtime.close()


def test_diagnostics_accept_real_executor(tmp_path: Path) -> None:
    def executor(_experiment: Experiment):
        return [{"score": 1.0}]

    factory = build_factory(tmp_path, executor)
    try:
        report = factory.diagnose()
        check = next(item for item in report["checks"] if item["name"] == "experiment_execution")
        assert check["status"] == "ok"
        assert check["evidence"]["validation_allowed"] is True
    finally:
        factory.runtime.close()

from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory
from aurelix_core.intelligence_flow import IntelligenceFlow
from aurelix_core.model_gateway import ModelProvider
from aurelix_runtime.integrated_engines import Evidence
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class FakeModelProvider(ModelProvider):
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "Validated lesson."

    def structured_output(self, prompt: str, schema: dict):
        return {
            "title": "Bounded automation",
            "problem": "Manual workflow",
            "proposed_solution": "Automate the bounded workflow",
            "expected_value": "Lower cycle time",
            "estimated_cost": 100.0,
            "risk": 2,
            "confidence": 0.9,
        }

    def embeddings(self, text: str) -> list[float]:
        return [1.0, 0.0]

    def health(self) -> bool:
        return True


def test_intelligence_flow_stops_at_real_observations(tmp_path: Path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    repository = InMemoryKnowledgeRepository()

    def provider(query: str):
        return [Evidence("https://example.test/source", f"Finding for {query}", 0.9, True)]

    factory = EngineFactory(
        runtime=runtime,
        model_provider=FakeModelProvider(),
        research_provider=provider,
        knowledge=repository,
    )
    flow = IntelligenceFlow(factory)

    result = flow.research_to_experiment("bounded automation")
    assert result["evidence_count"] == 1
    assert repository.count() == 1
    experiment_id = result["experiment"]["experiment_id"]

    execution = flow.execute_experiment(experiment_id, [{"success": 1.0}])
    assert execution["status"] == "complete"
    assert execution["evaluation"]["passed"] is True
    assert execution["evaluation"]["confidence"] == 1.0

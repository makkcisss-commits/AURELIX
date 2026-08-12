from __future__ import annotations

from pathlib import Path

from aurelix_core.engine_factory import EngineFactory
from aurelix_core.model_gateway import ModelProvider
from aurelix_runtime.integrated_engines import EngineStore, Evidence
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class FakeModelProvider(ModelProvider):
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "Validated lesson synthesized from the supplied evidence."

    def structured_output(self, prompt: str, schema: dict):
        return {
            "title": "Evidence-backed automation opportunity",
            "problem": "A validated workflow remains manual.",
            "proposed_solution": "Automate the bounded workflow.",
            "expected_value": "Reduce cycle time.",
            "estimated_cost": 100.0,
            "risk": 2,
            "confidence": 0.8,
        }

    def embeddings(self, text: str) -> list[float]:
        return [1.0, 0.0]

    def health(self) -> bool:
        return True


def test_research_knowledge_innovation_experiment_evaluation(tmp_path: Path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db")))
    repository = InMemoryKnowledgeRepository()

    def research_provider(query: str):
        return [Evidence("https://example.test/source", f"Source-backed finding for {query}", 0.9, True)]

    factory = EngineFactory(
        runtime=runtime,
        model_provider=FakeModelProvider(),
        research_provider=research_provider,
        knowledge=repository,
    )
    store = EngineStore()

    research = factory.research_and_store("bounded automation")
    assert len(research.evidence) == 1
    assert repository.count() == 1
    assert repository.search(KnowledgeQuery("source-backed finding", limit=10))

    academy = factory.academy.run({"objective": "bounded automation", "evidence": list(research.evidence)}, store)
    assert academy["lessons"]

    knowledge = factory.knowledge_engine.run(academy, store)
    innovation = factory.innovation.run(knowledge, store)
    experiment_payload = factory.experiment.run(innovation, store)
    experiment = store.experiments[experiment_payload["experiment_id"]]

    runtime.register_experiment(experiment)
    runtime.record_observation(experiment.id, {"success": 1.0})
    run = factory.experiment_runner.execute(experiment)

    assert run.status == "complete"
    assert run.evaluation is not None
    assert run.evaluation.passed is True
    assert run.evaluation.confidence == 1.0
    assert runtime.query_experiments("complete")[0]["result"]["passed"] is True

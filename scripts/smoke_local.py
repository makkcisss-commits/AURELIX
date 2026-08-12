from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aurelix_core.engine_factory import EngineFactory
from aurelix_core.model_gateway import ModelProvider
from aurelix_runtime.integrated_engines import Evidence
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


class SmokeModelProvider(ModelProvider):
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        return "Validated lesson synthesized from supplied evidence."

    def structured_output(self, prompt: str, schema: dict) -> dict:
        return {
            "title": "Evidence-backed automation opportunity",
            "problem": "A bounded workflow remains manual.",
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


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="aurelix-smoke-") as directory:
        runtime = AurelixRuntime(RuntimeConfig(database_path=str(Path(directory) / "runtime.db")))
        knowledge = InMemoryKnowledgeRepository()

        def research_provider(query: str) -> list[Evidence]:
            return [Evidence("https://example.test/source", f"Verified finding for {query}", 0.95, True)]

        factory = EngineFactory(
            runtime=runtime,
            model_provider=SmokeModelProvider(),
            research_provider=research_provider,
            knowledge=knowledge,
        )

        result = factory.research_and_store("local smoke test")
        assert result.evidence
        assert knowledge.count() == 1
        assert knowledge.search(KnowledgeQuery("Verified finding", limit=10))

        from aurelix_runtime.integrated_engines import EngineStore

        store = EngineStore()
        academy = factory.academy.run({"objective": result.query, "evidence": list(result.evidence)}, store)
        knowledge_result = factory.knowledge_engine.run(academy, store)
        innovation = factory.innovation.run(knowledge_result, store)
        experiment_payload = factory.experiment.run(innovation, store)
        experiment = store.experiments[experiment_payload["experiment_id"]]

        runtime.register_experiment(experiment)
        runtime.record_observation(experiment.id, {"success": 1.0})
        run = factory.experiment_runner.execute(experiment)

        assert run.status == "complete"
        assert run.evaluation is not None
        assert run.evaluation.passed is True

        print(json.dumps({
            "status": "ok",
            "evidence_count": len(result.evidence),
            "knowledge_count": knowledge.count(),
            "experiment_id": experiment.id,
            "evaluation": {
                "passed": run.evaluation.passed,
                "confidence": run.evaluation.confidence,
                "reasons": list(run.evaluation.reasons),
            },
        }, indent=2))


if __name__ == "__main__":
    main()

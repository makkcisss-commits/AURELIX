from __future__ import annotations

import json
import tempfile
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from aurelix_core.economic_opportunity_validation import qualify_opportunity
from aurelix_core.evidence import EvidenceRelation, make_evidence
from aurelix_core.opportunity_execution_bridge import OpportunityExecutionBridge
from aurelix_core.opportunities import OpportunityStage, build_opportunity
from aurelix_core.resource_scope import ResourceKind, ResourcePermission
from aurelix_runtime.integrated_engines import EngineStore, Evidence
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeQuery
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from .engine_factory import EngineFactory
from .model_gateway import ModelProvider


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

        factory = EngineFactory(runtime=runtime, model_provider=SmokeModelProvider(), research_provider=research_provider, knowledge=knowledge)
        result = factory.research_and_store("local smoke test")
        assert result.evidence
        assert knowledge.count() == 1
        assert knowledge.search(KnowledgeQuery("Verified finding", limit=10))

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

        opportunity = build_opportunity(title="Bounded paid automation", finding_ids=[result.evidence[0].evidence_id], cost_eur=Decimal("20"), monthly_revenue_eur=Decimal("300"), hours=Decimal("4"), complexity=2, risk=1, confidence=Decimal("0.9"))
        evidence_by_claim = {claim: [make_evidence(source_ref="https://example.test/source", claim=f"Supported {claim}", relation=EvidenceRelation.SUPPORTS, quality=Decimal("0.95"))] for claim in ("demand", "monetization_path", "source_reality")}
        qualification = qualify_opportunity(opportunity, evidence_by_claim=evidence_by_claim)
        assert qualification.is_qualified
        approved = replace(opportunity, stage=OpportunityStage.APPROVED)

        actor_id = "smoke-business-agent"
        permission = ResourcePermission(actor_id=actor_id, resource=ResourceKind.BUSINESS, operations=frozenset({"execute"}), scope=approved.opportunity_id)
        bridge = OpportunityExecutionBridge()
        outcome = bridge.execute(approved, qualification=qualification, actor_id=actor_id, owner_role="business", channel="smoke-channel", permission=permission, operation=lambda: {"revenue_eur": "125.50", "external_reference": "smoke-payment"})
        assert outcome.executed is True
        assert outcome.observed_revenue_eur == Decimal("125.50")
        assert outcome.revenue_source_id is not None
        source = bridge.revenue.sources[outcome.revenue_source_id]
        assert source.is_productive is True
        assert source.observed_daily_eur == Decimal("125.50")

        print(json.dumps({"status": "ok", "evidence_count": len(result.evidence), "knowledge_count": knowledge.count(), "experiment_id": experiment.id, "economic_path": {"qualified": qualification.is_qualified, "executed": outcome.executed, "observed_revenue_eur": str(outcome.observed_revenue_eur), "productive_source": source.is_productive}}, indent=2))

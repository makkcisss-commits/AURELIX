"""Unified AURELIX orchestration across intelligence, learning and governance.

This boundary composes existing engines instead of creating a second authority
model. It can run continuously, but protected execution still terminates at
Governor/ControlPlane/ExecutionGate boundaries.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Any

from .academy import AcademyEngine as CuratedAcademy
from .academy_governor_boundary import AcademyGovernorBoundary, AcademyProposal
from .academy_intelligence_bridge import AcademyIntelligenceBridge
from .continuous_intelligence import ContinuousIntelligence
from .economic_attribution import EconomicAttribution, EconomicAttributionLedger
from .governor import Governor
from .learning import LearningEngine, Outcome
from .verified_economic_learning import VerifiedEconomicLearning


@dataclass(frozen=True)
class SystemCycleResult:
    objective: str
    status: str
    enterprise: dict[str, Any]
    intelligence: dict[str, Any]
    governance: dict[str, Any]
    economic_learning: dict[str, Any]
    diagnostics: dict[str, Any]


class SystemOrchestrator:
    """One coordinator for the complete safe autonomous lifecycle."""

    def __init__(self, factory) -> None:
        self.factory = factory
        self.intelligence = ContinuousIntelligence()
        self.curated_academy = CuratedAcademy()
        self.academy_bridge = AcademyIntelligenceBridge(self.intelligence)
        self.proposal_boundary = AcademyGovernorBoundary()
        self.economic_ledger = EconomicAttributionLedger()
        self.verified_learning = VerifiedEconomicLearning(self.economic_ledger)
        self.learning = LearningEngine()
        self.governor = factory.governor if hasattr(factory, "governor") else Governor()
        self._proposals: dict[str, AcademyProposal] = {}

    def run_cycle(self, objective: str) -> SystemCycleResult:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective is required")

        enterprise = self.factory.enterprise.run(objective, approved=False)
        enterprise_dict = asdict(enterprise)
        academy_payload = enterprise_dict["academy"]
        knowledge_payload = enterprise_dict["knowledge"]

        intelligence = self._project_academy(academy_payload, knowledge_payload, objective)
        governance = self._govern_proposal(intelligence, objective)
        economic = self._emit_economic_learning()
        diagnostics = self._diagnostics()

        status = "attention" if governance.get("route") == "BLOCKED" else enterprise.status
        result = SystemCycleResult(
            objective=objective,
            status=status,
            enterprise=enterprise_dict,
            intelligence=intelligence,
            governance=governance,
            economic_learning=economic,
            diagnostics=diagnostics,
        )
        self.factory.runtime.store.audit(
            "system.cycle.completed",
            "system_orchestrator",
            objective,
            status,
            {"governance_route": governance.get("route"), "new_learning": economic["new_signals"]},
        )
        return result

    def record_verified_economic_outcome(
        self,
        *,
        opportunity_id: str,
        source_id: str,
        expected_daily_eur: Decimal,
        observed_daily_eur: Decimal,
        governor_decision_id: str,
        resource_scope: str | None = None,
        external_reference: str | None = None,
    ) -> EconomicAttribution:
        """Record real realized economics; forecasts can never enter this path."""
        entry = self.economic_ledger.record(
            opportunity_id=opportunity_id,
            source_id=source_id,
            expected_daily_eur=expected_daily_eur,
            observed_daily_eur=observed_daily_eur,
            governor_decision_id=governor_decision_id,
            resource_scope=resource_scope,
            verified=True,
            external_reference=external_reference,
        )
        self.factory.runtime.store.audit(
            "economic.attribution.recorded",
            "economic_ledger",
            opportunity_id,
            "verified",
            {"source_id": source_id, "governor_decision_id": governor_decision_id},
        )
        return entry

    def status(self) -> dict[str, Any]:
        runtime = self.factory.runtime
        return {
            "runtime": runtime.store.status(),
            "economic_learning": self.verified_learning.learning_context(),
            "learning_items": len(self.learning._items),
            "proposal_count": len(self._proposals),
            "intelligence": {
                "domains": len(self.intelligence.domains),
                "objectives": len(self.intelligence.objectives),
                "evidence": len(self.intelligence.evidence),
                "knowledge": len(self.intelligence.knowledge),
            },
        }

    def _project_academy(self, academy_payload: dict[str, Any], knowledge_payload: dict[str, Any], objective: str) -> dict[str, Any]:
        knowledge_id = knowledge_payload.get("knowledge_id")
        lessons = [str(item) for item in academy_payload.get("lessons", []) if str(item).strip()]
        evidence = list(academy_payload.get("evidence", []))
        if not knowledge_id or not lessons:
            return {"status": "awaiting_knowledge", "knowledge_id": knowledge_id, "objective": objective}

        source_refs = []
        for item in evidence:
            source = item.get("source") if isinstance(item, dict) else getattr(item, "source", "")
            if source:
                source_refs.append(str(source))
        curated = self.curated_academy.create_knowledge(
            title=f"AURELIX Academy: {objective[:120]}",
            summary="\n".join(lessons),
            learning_refs=[str(knowledge_id)],
            source_refs=source_refs or [str(knowledge_id)],
            confidence=1.0 if knowledge_payload.get("validated") else 0.5,
        )
        item, projection = self.academy_bridge.project_knowledge(curated, domain="general")
        return {
            "status": "projected",
            "knowledge_id": item.knowledge_id,
            "objective_id": projection.objective_id,
            "evidence_ids": list(projection.evidence_ids),
            "domain": projection.domain,
            "confidence": item.confidence,
        }

    def _govern_proposal(self, intelligence: dict[str, Any], objective: str) -> dict[str, Any]:
        if intelligence.get("status") != "projected":
            return {"route": "BLOCKED", "reason": "no validated academy knowledge"}
        proposal = self.proposal_boundary.propose(
            knowledge_id=intelligence["knowledge_id"],
            title=f"Academy proposal: {objective[:100]}",
            rationale=f"Traceable proposal derived from {len(intelligence['evidence_ids'])} evidence records.",
            learning_refs=intelligence["evidence_ids"],
        )
        self._proposals[proposal.proposal_id] = proposal
        decision = self.governor.route(
            source="academy",
            action="proposal.review",
            requires_capital=False,
            risk=2,
            production_change=False,
        )
        return {
            "proposal_id": proposal.proposal_id,
            "route": decision.route.value,
            "request_id": decision.request_id,
            "reasons": list(decision.reasons),
            "execution_allowed": False,
        }

    def _emit_economic_learning(self) -> dict[str, Any]:
        fresh = self.verified_learning.emit()
        learning_items = []
        for signal in fresh:
            outcome = Outcome.SUCCESS if signal.observed_daily_eur > 0 else Outcome.FAILURE
            observation = (
                f"Observed {signal.observed_daily_eur} EUR/day versus expected "
                f"{signal.expected_daily_eur} EUR/day; variance {signal.variance_daily_eur} EUR/day."
            )
            learning = self.learning.record(
                experiment_id=f"economic:{signal.opportunity_id}:{signal.source_id}",
                outcome=outcome,
                observation=observation,
                evidence_refs=[
                    signal.opportunity_id,
                    signal.source_id,
                    signal.governor_decision_id,
                    *([signal.external_reference] if signal.external_reference else []),
                ],
                confidence=1.0,
            )
            learning_items.append({
                "learning_id": learning.learning_id,
                "experiment_id": learning.experiment_id,
                "outcome": learning.outcome.value,
                "evidence_refs": list(learning.evidence_refs),
            })

        context = self.verified_learning.learning_context()
        context["learning_item_count"] = len(learning_items)
        context["rule"] = (
            "only verified realized economics may become learning evidence; "
            "learning remains observational and cannot authorize execution"
        )
        return {
            "new_signals": len(fresh),
            "learning_items": learning_items,
            "signals": [
                {
                    "opportunity_id": signal.opportunity_id,
                    "source_id": signal.source_id,
                    "governor_decision_id": signal.governor_decision_id,
                    "resource_scope": signal.resource_scope,
                    "expected_daily_eur": str(signal.expected_daily_eur),
                    "observed_daily_eur": str(signal.observed_daily_eur),
                    "variance_daily_eur": str(signal.variance_daily_eur),
                    "realization_ratio": str(signal.realization_ratio),
                    "evidence_type": signal.evidence_type,
                    "verified": signal.verified,
                }
                for signal in fresh
            ],
            "context": context,
        }

    def _diagnostics(self) -> dict[str, Any]:
        try:
            validation = self.factory.validate_system()
            return {"status": validation.get("status", "unknown"), "summary": validation.get("summary", {})}
        except Exception as exc:
            return {"status": "degraded", "error": type(exc).__name__}
